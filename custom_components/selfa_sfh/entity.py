"""Shared device identity and coordinator subscription."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class SelfaEntity(CoordinatorEntity):
    """Preserve the original entry-based measurement unique IDs."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            manufacturer="Selfa",
            model="SFH",
            name="Selfa SFH",
            serial_number=data.get("serial_number")
            or self.coordinator.entry.data.get("serial_number"),
            sw_version=str(data["firmware_version"])
            if data.get("firmware_version") is not None
            else None,
        )

    @property
    def extra_state_attributes(self):
        return {"selfa_key": self.key}

    @property
    def available(self) -> bool:
        return super().available and (self.coordinator.data or {}).get(self.key) is not None
