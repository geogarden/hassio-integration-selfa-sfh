"""Select platform for Selfa SFH Hybrid Inverter — Working Mode control."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_WORKING_MODE, WORKING_MODE_OPTIONS
from .coordinator import SelfahybridCoordinator

# Reverse map: raw value → label
_VALUE_TO_LABEL = {v: k for k, v in WORKING_MODE_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SelfahybridCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SelfahybridWorkingModeSelect(coordinator)])


class SelfahybridWorkingModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for inverter working mode."""

    _attr_name = "Inverter Working Mode"
    _attr_icon = "mdi:cog-transfer"
    _attr_options = list(WORKING_MODE_OPTIONS.keys())

    def __init__(self, coordinator: SelfahybridCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_working_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Selfa SFH Hybrid Inverter",
            "manufacturer": "Selfa",
            "model": "SFH",
        }

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get("working_mode")
        return _VALUE_TO_LABEL.get(raw)

    async def async_select_option(self, option: str) -> None:
        value = WORKING_MODE_OPTIONS.get(option)
        if value is None:
            return
        await self.coordinator.client.write_register(REG_WORKING_MODE, value)
        await self.coordinator.async_request_refresh()
