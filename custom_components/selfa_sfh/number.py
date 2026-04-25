"""Number platform for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_GRID_INJ_LIMIT
from .coordinator import SelfahybridCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SelfahybridCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SelfahybridGridInjLimitNumber(coordinator)])


class SelfahybridGridInjLimitNumber(CoordinatorEntity, NumberEntity):
    """Number entity for Grid Injection Power Limit (%)."""

    _attr_name = "Grid Injection Power Limit"
    _attr_icon = "mdi:transmission-tower-export"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SelfahybridCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_grid_inj_limit"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Selfa SFH Hybrid Inverter",
            "manufacturer": "Selfa",
            "model": "SFH",
        }

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("grid_inj_limit")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.write_register(REG_GRID_INJ_LIMIT, int(value))
        await self.coordinator.async_request_refresh()
