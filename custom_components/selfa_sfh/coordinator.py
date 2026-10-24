"""Share all documented readings and handle unsupported optional registers."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta

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
