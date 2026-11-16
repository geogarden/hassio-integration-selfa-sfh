"""Manually retry optional firmware readings without restarting HA."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import SelfaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SelfaRetryButton(entry.runtime_data, "retry_registers"),
                        SelfaClockButton(entry.runtime_data, "sync_clock"),
                        *[SelfaCommandButton(entry.runtime_data, key) for key in
                          ("off_grid_on", "off_grid_off", "clear_off_grid_overload")]])


class SelfaRetryButton(SelfaEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_retry_registers()


class SelfaClockButton(SelfaEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-check-outline"

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_press(self):
        await self.coordinator.async_sync_clock()


class SelfaCommandButton(SelfaEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:tools"

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.service_controls

    async def async_press(self):
        await self.coordinator.async_wo_command(self.key)
