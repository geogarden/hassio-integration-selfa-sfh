"""Manually retry optional firmware readings without restarting HA."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import SelfaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SelfaRetryButton(entry.runtime_data, "retry_registers")])


class SelfaRetryButton(SelfaEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_retry_registers()
