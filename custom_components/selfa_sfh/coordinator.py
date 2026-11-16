"""Share all documented readings and handle unsupported optional registers."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from decimal import Decimal

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_SETTINGS_INTERVAL,
    CONTROL_REGISTERS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SETTINGS_INTERVAL,
    DOMAIN,
)
from .controls import BY_KEY, validate_period
from .modbus_client import (
    SelfaConnectionError,
    SelfahybridModbusClient,
    SelfaRegisterError,
)
from .registers import Register, decode_value, read_blocks

_LOGGER = logging.getLogger(__name__)


class SelfahybridCoordinator(DataUpdateCoordinator[dict]):
    """Serialise polls and intentional writes on the same RS485 bus."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: SelfahybridModbusClient,
        registers: tuple[Register, ...],
    ) -> None:
        self.entry = entry
        options = {**entry.data, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client, self.registers = client, registers
        self.settings_interval = options.get(CONF_SETTINGS_INTERVAL, DEFAULT_SETTINGS_INTERVAL)
        self.unsupported: set[str] = set()
        self._slow_values: dict = {}
        self._slow_at = 0.0
        self._bus = asyncio.Lock()
        self.last_success = None
        self._register_by_address = {reg.address: reg for reg in registers}
        self.power_limit = float(options.get("control_power_limit_kw", 0))
        self.service_controls = bool(options.get("service_controls", False))
        self.ems_controls = bool(options.get("ems_controls", False))

    async def _read_group(self, group: list[Register], words: dict[int, int]) -> None:
        first, last = group[0], group[-1]
        try:
            values = await self.client.read_registers(
                first.address, last.address + last.count - first.address
            )
        except SelfaRegisterError as err:
            if err.code not in (2, 3):
                raise
            if len(group) == 1:
                if first.key == "working_status_raw":
                    raise
                self.unsupported.add(first.key)
                _LOGGER.debug("Unsupported register: %s (%s)", first.address, first.key)
            else:
                for register in group:
                    await self._read_group([register], words)
            return
        words.update({first.address + i: word for i, word in enumerate(values)})

    async def _async_update_data(self) -> dict:
        async with self._bus:
            slow_due = (
                not self._slow_at or time.monotonic() - self._slow_at >= self.settings_interval
            )
            selected = [
                reg
                for reg in self.registers
                if reg.key not in self.unsupported and (not reg.slow or slow_due)
            ]
            words: dict[int, int] = {}
            try:
                for group in read_blocks(selected):
                    await self._read_group(group, words)
            except (SelfaConnectionError, SelfaRegisterError) as err:
                await self.client.disconnect()
                raise UpdateFailed(f"Selfa Modbus: {err}") from err
            values = {register.key: decode_value(register, words) for register in selected}
            if values.get("working_status_raw") is None:
                raise UpdateFailed("No working status returned by the inverter (10105)")
            if slow_due:
                self._slow_values = {
                    reg.key: values.get(reg.key) for reg in self.registers if reg.slow
                }
                self._slow_at = time.monotonic()
            result = {**self._slow_values, **values}
            for key in self.unsupported:
                result[key] = None
            self.last_success = dt_util.utcnow()
            return result

    async def async_set_switch(self, key: str, enabled: bool) -> None:
        """Only two documented 0/1 switches can be written."""
        if key not in CONTROL_REGISTERS:
            raise HomeAssistantError("Arbitrary Modbus writes are not exposed")
        async with self._bus:
            try:
                value = await self.client.write_and_confirm(CONTROL_REGISTERS[key], int(enabled))
            except (SelfaConnectionError, SelfaRegisterError) as err:
                raise HomeAssistantError(f"Selfa did not confirm the change: {err}") from err
            self._slow_values[key] = value
            if self.data is not None:
                self.async_set_updated_data({**self.data, key: value})

    async def async_retry_registers(self) -> None:
        """Retry unsupported optional readings on demand."""
        async with self._bus:
            self.unsupported.clear()
            self._slow_at = 0.0
        await self.async_request_refresh()


    def control_raw(self, address):
        reg = self._register_by_address.get(address)
        value = (self.data or {}).get(reg.key) if reg else None
        if value is None:
            return None
        return int(Decimal(str(value)) * reg.divisor) & 65535

    def control_available(self, control):
        return (self.control_raw(control.address) is not None
                and (not control.advanced or self.service_controls)
                and (not control.power or self.power_limit > 0)
                and (control.key != "battery_protocol_control" or self.control_raw(52500) == 1))

    def _store_confirmed(self, address, raw):
        reg = self._register_by_address[address]
        value = raw - 65536 if reg.data_type == "I16" and raw & 32768 else raw
        value = value / reg.divisor if reg.divisor != 1 else value
        self._slow_values[reg.key] = value
        self.async_set_updated_data({**(self.data or {}), reg.key: value})

    async def async_set_control(self, key, value):
        if key not in BY_KEY:
            raise HomeAssistantError("Unknown control")
        control = BY_KEY[key]
        if not self.last_update_success or not self.control_available(control):
            raise HomeAssistantError("Control is unavailable or disabled in integration options")
        try:
            raw = control.encode(value)
            if control.power and abs(float(value)) > self.power_limit:
                raise ValueError("Power exceeds the commissioned installation limit")
            if key == "operating_mode" and str(value).startswith("ems_") and not self.ems_controls:
                raise ValueError("Enable expert EMS mode selection in integration options first")
            async with self._bus:
                # Always use live values for read-modify-write operations.
                if control.bit is not None:
                    current = (await self.client.read_registers(control.address, 1))[0]
                    if value:
                        base = 53007 + control.bit * 7
                        start, end = await self.client.read_registers(base + 5, 2)
                        validate_period(start, end)
                    raw = current | (1 << control.bit) if value else current & ~(1 << control.bit)
                elif key.startswith("period_") and control.kind == "time":
                    slot = int(key.split("_")[1]) - 1
                    mask = (await self.client.read_registers(53006, 1))[0]
                    if mask & (1 << slot):
                        raise ValueError("Disable this period before editing its times")
                if key in ("ac_upper_limit", "ac_lower_limit"):
                    other = 50209 if key == "ac_upper_limit" else 50208
                    other_raw = (await self.client.read_registers(other, 1))[0]
                    other_value = BY_KEY["ac_lower_limit" if other == 50209 else "ac_upper_limit"].decode(other_raw)
                    if (key == "ac_upper_limit" and value < other_value) or (key == "ac_lower_limit" and value > other_value):
                        raise ValueError("Lower AC limit must not exceed upper AC limit")
                result = await self.client.write_and_confirm(control.address, raw)
                self._store_confirmed(control.address, result)
        except (ValueError, SelfaConnectionError, SelfaRegisterError) as err:
            raise HomeAssistantError(f"Selfa setting was not confirmed: {err}") from err

    async def async_sync_clock(self):
        if not self.last_update_success:
            raise HomeAssistantError("Inverter unavailable")
        now = dt_util.now()
        if not 2019 <= now.year <= 2099:
            raise HomeAssistantError("RTC supports years 2019–2099")
        values = {20000: ((now.year % 100) << 8) | now.month,
                  20001: (now.day << 8) | now.hour,
                  20002: (now.minute << 8) | now.second}
        async with self._bus:
            try:
                for address, value in values.items():
                    result = await self.client.write_and_confirm(address, value)
                    self._store_confirmed(address, result)
            except (SelfaConnectionError, SelfaRegisterError) as err:
                raise HomeAssistantError(f"Clock update stopped; some fields may have changed: {err}") from err

    async def async_wo_command(self, command):
        commands = {"off_grid_on": (50200, 1), "off_grid_off": (50200, 0), "clear_off_grid_overload": (50201, 1)}
        if not self.service_controls or not self.last_update_success or command not in commands:
            raise HomeAssistantError("Service command disabled or inverter unavailable")
        async with self._bus:
            try:
                await self.client.write_command(*commands[command])
            except (SelfaConnectionError, SelfaRegisterError) as err:
                raise HomeAssistantError(f"Command not acknowledged: {err}") from err
        await self.async_request_refresh()
