"""Common entity for translated, confirmed configuration controls."""
from homeassistant.helpers.entity import EntityCategory

from .entity import SelfaEntity


class SelfaControlEntity(SelfaEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, control):
        super().__init__(coordinator, control.key)
        self.control = control
        self._attr_entity_registry_enabled_default = not control.advanced

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.control_available(self.control)

    @property
    def extra_state_attributes(self):
        return {**super().extra_state_attributes, "register": self.control.address}

    def control_value(self):
        raw = self.coordinator.control_raw(self.control.address)
        return None if raw is None else self.control.decode(raw)

    async def write(self, value):
        await self.coordinator.async_set_control(self.control.key, value)
