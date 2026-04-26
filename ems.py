"""EMS control platform for Selfa SFH Hybrid Inverter.

Provides:
- EMS Number entities for power setpoints (AC ctrl, battery charge/discharge)
- HA services for advanced EMS commands
- Automatic keepalive writer (writes meter/BMS data periodically)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    WORKING_MODE_EMS_ACC,
    WORKING_MODE_EMS_GEN,
    WORKING_MODE_EMS_BAT,
    WORKING_MODE_EMS_OFF,
    REG_WORKING_MODE,
    REG_EMS_AC_CTRL_TOTAL,
    REG_EMS_AC_CTRL_A,
    REG_EMS_AC_CTRL_B,
    REG_EMS_AC_CTRL_C,
    REG_EMS_GENERAL_MODE,
    REG_EMS_BAT_CHG_PBAT,
    REG_EMS_BAT_CHG_UP_LIMIT,
    REG_EMS_BAT_CHG_LOW_LIMIT,
    REG_EMS_BAT_DCHG_PBAT,
    REG_EMS_BAT_DCHG_UP_LIMIT,
    REG_EMS_BAT_DCHG_LOW_LIM,
    REG_EMS_BAT_FORCE_CHG_PBAT,
    REG_EMS_BAT_FORCE_CHG_UP,
    REG_EMS_BAT_FORCE_CHG_LOW,
    REG_EMS_BAT_FORCE_DCHG_PBAT,
    REG_EMS_BAT_FORCE_DCHG_UP,
    REG_EMS_BAT_FORCE_DCHG_LOW,
    REG_EMS_OFF_GRID_PV_POWER,
)
from .coordinator import SelfahybridCoordinator

_LOGGER = logging.getLogger(__name__)

# ── Helper ───────────────────────────────────────────────────────────────────

def _kw_to_reg(kw: float) -> int:
    """Convert kW (float) to register value (×10, signed 32-bit split into 2 regs)."""
    return int(round(kw * 10))


async def _write_i32(coordinator: SelfahybridCoordinator, address: int, kw: float) -> bool:
    """Write a signed 32-bit value (2 registers) for a power setpoint in kW."""
    raw = _kw_to_reg(kw)
    # Treat as unsigned 32-bit for Modbus
    if raw < 0:
        raw = raw & 0xFFFFFFFF
    hi = (raw >> 16) & 0xFFFF
    lo = raw & 0xFFFF
    ok1 = await coordinator.client.write_register(address, hi)
    ok2 = await coordinator.client.write_register(address + 1, lo)
    return ok1 and ok2


# ── EMS Number entities ──────────────────────────────────────────────────────

@dataclass
class EMSNumberDescription:
    key: str
    name: str
    icon: str
    register: int
    is_i32: bool = False   # True = write as 2-register I32
    min_value: float = -30.0
    max_value: float = 30.0
    step: float = 0.1


EMS_NUMBER_DESCRIPTIONS: tuple[EMSNumberDescription, ...] = (
    # EMS AC Control
    EMSNumberDescription(
        key="ems_ac_total",
        name="EMS AC Total Power Setpoint",
        icon="mdi:transmission-tower",
        register=REG_EMS_AC_CTRL_TOTAL,
        is_i32=True,
        min_value=-30.0,
        max_value=30.0,
    ),
    EMSNumberDescription(
        key="ems_ac_phase_a",
        name="EMS AC Phase A Power Setpoint",
        icon="mdi:alpha-a-circle",
        register=REG_EMS_AC_CTRL_A,
        is_i32=True,
        min_value=-15.0,
        max_value=15.0,
    ),
    EMSNumberDescription(
        key="ems_ac_phase_b",
        name="EMS AC Phase B Power Setpoint",
        icon="mdi:alpha-b-circle",
        register=REG_EMS_AC_CTRL_B,
        is_i32=True,
        min_value=-15.0,
        max_value=15.0,
    ),
    EMSNumberDescription(
        key="ems_ac_phase_c",
        name="EMS AC Phase C Power Setpoint",
        icon="mdi:alpha-c-circle",
        register=REG_EMS_AC_CTRL_C,
        is_i32=True,
        min_value=-15.0,
        max_value=15.0,
    ),
    # EMS General Mode
    EMSNumberDescription(
        key="ems_general_target",
        name="EMS General Mode Power Target",
        icon="mdi:home-lightning-bolt",
        register=REG_EMS_GENERAL_MODE,
        is_i32=True,
        min_value=-30.0,
        max_value=30.0,
    ),
    # EMS Battery Charge
    EMSNumberDescription(
        key="ems_bat_chg_power",
        name="EMS Battery Charge Power (Pbat)",
        icon="mdi:battery-arrow-up",
        register=REG_EMS_BAT_CHG_PBAT,
        is_i32=True,
        min_value=0.0,
        max_value=30.0,
    ),
    EMSNumberDescription(
        key="ems_bat_chg_up_limit",
        name="EMS Battery Charge Grid Import Upper Limit",
        icon="mdi:arrow-up-bold",
        register=REG_EMS_BAT_CHG_UP_LIMIT,
        is_i32=False,
        min_value=0.0,
        max_value=30.0,
    ),
    EMSNumberDescription(
        key="ems_bat_chg_low_limit",
        name="EMS Battery Charge Grid Import Lower Limit",
        icon="mdi:arrow-down-bold",
        register=REG_EMS_BAT_CHG_LOW_LIMIT,
        is_i32=False,
        min_value=-30.0,
        max_value=0.0,
    ),
    # EMS Battery Discharge
    EMSNumberDescription(
        key="ems_bat_dchg_power",
        name="EMS Battery Discharge Power (Pbat)",
        icon="mdi:battery-arrow-down",
        register=REG_EMS_BAT_DCHG_PBAT,
        is_i32=True,
        min_value=0.0,
        max_value=30.0,
    ),
    EMSNumberDescription(
        key="ems_bat_dchg_up_limit",
        name="EMS Battery Discharge Grid Inject Upper Limit",
        icon="mdi:arrow-up-bold-outline",
        register=REG_EMS_BAT_DCHG_UP_LIMIT,
        is_i32=False,
        min_value=0.0,
        max_value=30.0,
    ),
    EMSNumberDescription(
        key="ems_bat_dchg_low_limit",
        name="EMS Battery Discharge Grid Inject Lower Limit",
        icon="mdi:arrow-down-bold-outline",
        register=REG_EMS_BAT_DCHG_LOW_LIM,
        is_i32=False,
        min_value=-30.0,
        max_value=0.0,
    ),
    # EMS Off-Grid
    EMSNumberDescription(
        key="ems_off_grid_pv",
        name="EMS Off-Grid PV Power Setpoint",
        icon="mdi:solar-panel",
        register=REG_EMS_OFF_GRID_PV_POWER,
        is_i32=True,
        min_value=0.0,
        max_value=30.0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EMS number entities and register HA services."""
    coordinator: SelfahybridCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EMSNumberEntity(coordinator, desc) for desc in EMS_NUMBER_DESCRIPTIONS
    )

    # ── Register HA services ─────────────────────────────────────────────────

    async def _svc_set_ac_ctrl(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_set_ac_control — set EMS AC Control mode."""
        total = call.data.get("total_power")
        phase_a = call.data.get("phase_a")
        phase_b = call.data.get("phase_b")
        phase_c = call.data.get("phase_c")

        # Switch to EMS AC Control mode first
        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_ACC)

        if total is not None:
            await _write_i32(coordinator, REG_EMS_AC_CTRL_TOTAL, total)
        if phase_a is not None:
            await _write_i32(coordinator, REG_EMS_AC_CTRL_A, phase_a)
        if phase_b is not None:
            await _write_i32(coordinator, REG_EMS_AC_CTRL_B, phase_b)
        if phase_c is not None:
            await _write_i32(coordinator, REG_EMS_AC_CTRL_C, phase_c)

        await coordinator.async_request_refresh()
        _LOGGER.info("EMS AC Control set: total=%s A=%s B=%s C=%s", total, phase_a, phase_b, phase_c)

    async def _svc_set_general(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_set_general — set EMS General mode power target."""
        power = call.data["power"]
        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_GEN)
        await _write_i32(coordinator, REG_EMS_GENERAL_MODE, power)
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS General Mode power target set to %s kW", power)

    async def _svc_set_bat_charge(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_set_battery_charge."""
        pbat = call.data["pbat"]
        up_limit = call.data.get("up_limit", 10.0)
        low_limit = call.data.get("low_limit", -10.0)

        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_BAT)
        await _write_i32(coordinator, REG_EMS_BAT_CHG_PBAT, pbat)
        await coordinator.client.write_register(REG_EMS_BAT_CHG_UP_LIMIT, _kw_to_reg(up_limit))
        await coordinator.client.write_register(REG_EMS_BAT_CHG_LOW_LIMIT, _kw_to_reg(low_limit))
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS Battery Charge: pbat=%s up=%s low=%s", pbat, up_limit, low_limit)

    async def _svc_set_bat_discharge(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_set_battery_discharge."""
        pbat = call.data["pbat"]
        up_limit = call.data.get("up_limit", 10.0)
        low_limit = call.data.get("low_limit", -10.0)

        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_BAT)
        await _write_i32(coordinator, REG_EMS_BAT_DCHG_PBAT, pbat)
        await coordinator.client.write_register(REG_EMS_BAT_DCHG_UP_LIMIT, _kw_to_reg(up_limit))
        await coordinator.client.write_register(REG_EMS_BAT_DCHG_LOW_LIM, _kw_to_reg(low_limit))
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS Battery Discharge: pbat=%s up=%s low=%s", pbat, up_limit, low_limit)

    async def _svc_force_charge(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_force_charge — force battery charge regardless of grid."""
        pbat = call.data["pbat"]
        up_limit = call.data.get("up_limit", 10.0)
        low_limit = call.data.get("low_limit", -10.0)

        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_BAT)
        await _write_i32(coordinator, REG_EMS_BAT_FORCE_CHG_PBAT, pbat)
        await coordinator.client.write_register(REG_EMS_BAT_FORCE_CHG_UP, _kw_to_reg(up_limit))
        await coordinator.client.write_register(REG_EMS_BAT_FORCE_CHG_LOW, _kw_to_reg(low_limit))
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS Force Charge: pbat=%s", pbat)

    async def _svc_force_discharge(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_force_discharge — force battery discharge."""
        pbat = call.data["pbat"]
        up_limit = call.data.get("up_limit", 10.0)
        low_limit = call.data.get("low_limit", -10.0)

        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_BAT)
        await _write_i32(coordinator, REG_EMS_BAT_FORCE_DCHG_PBAT, pbat)
        await coordinator.client.write_register(REG_EMS_BAT_FORCE_DCHG_UP, _kw_to_reg(up_limit))
        await coordinator.client.write_register(REG_EMS_BAT_FORCE_DCHG_LOW, _kw_to_reg(low_limit))
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS Force Discharge: pbat=%s", pbat)

    async def _svc_off_grid(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_set_off_grid — EMS Off-Grid mode PV scheduling."""
        ppv = call.data["ppv"]
        await coordinator.client.write_register(REG_WORKING_MODE, WORKING_MODE_EMS_OFF)
        await _write_i32(coordinator, REG_EMS_OFF_GRID_PV_POWER, ppv)
        await coordinator.async_request_refresh()
        _LOGGER.info("EMS Off-Grid PV setpoint set to %s kW", ppv)

    async def _svc_restore_auto(call: ServiceCall) -> None:
        """Service: selfa_sfh.ems_restore_auto — exit EMS, go back to General Mode."""
        mode = call.data.get("mode", 0x0000)
        await coordinator.client.write_register(REG_WORKING_MODE, mode)
        await coordinator.async_request_refresh()
        _LOGGER.info("Restored inverter to mode 0x%04X", mode)

    _POWER_SCHEMA = vol.Schema({
        vol.Required("pbat"): vol.Coerce(float),
        vol.Optional("up_limit", default=10.0): vol.Coerce(float),
        vol.Optional("low_limit", default=-10.0): vol.Coerce(float),
    })

    hass.services.async_register(
        DOMAIN, "ems_set_ac_control",
        _svc_set_ac_ctrl,
        schema=vol.Schema({
            vol.Optional("total_power"): vol.Coerce(float),
            vol.Optional("phase_a"): vol.Coerce(float),
            vol.Optional("phase_b"): vol.Coerce(float),
            vol.Optional("phase_c"): vol.Coerce(float),
        }),
    )
    hass.services.async_register(
        DOMAIN, "ems_set_general",
        _svc_set_general,
        schema=vol.Schema({vol.Required("power"): vol.Coerce(float)}),
    )
    hass.services.async_register(DOMAIN, "ems_set_battery_charge",    _svc_set_bat_charge,    schema=_POWER_SCHEMA)
    hass.services.async_register(DOMAIN, "ems_set_battery_discharge", _svc_set_bat_discharge, schema=_POWER_SCHEMA)
    hass.services.async_register(DOMAIN, "ems_force_charge",          _svc_force_charge,      schema=_POWER_SCHEMA)
    hass.services.async_register(DOMAIN, "ems_force_discharge",       _svc_force_discharge,   schema=_POWER_SCHEMA)
    hass.services.async_register(
        DOMAIN, "ems_set_off_grid",
        _svc_off_grid,
        schema=vol.Schema({vol.Required("ppv"): vol.Coerce(float)}),
    )
    hass.services.async_register(
        DOMAIN, "ems_restore_auto",
        _svc_restore_auto,
        schema=vol.Schema({vol.Optional("mode", default=0): int}),
    )


class EMSNumberEntity(CoordinatorEntity, NumberEntity):
    """Numeric EMS setpoint entity."""

    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: SelfahybridCoordinator,
        desc: EMSNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{desc.key}"
        self._attr_name = desc.name
        self._attr_icon = desc.icon
        self._attr_native_min_value = desc.min_value
        self._attr_native_max_value = desc.max_value
        self._attr_native_step = desc.step
        self._current_value: float | None = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Selfa SFH Hybrid Inverter",
            "manufacturer": "Selfa",
            "model": "SFH",
        }

    @property
    def native_value(self) -> float | None:
        return self._current_value

    async def async_set_native_value(self, value: float) -> None:
        if self._desc.is_i32:
            await _write_i32(self.coordinator, self._desc.register, value)
        else:
            await self.coordinator.client.write_register(
                self._desc.register, _kw_to_reg(value)
            )
        self._current_value = value
        self.async_write_ha_state()
