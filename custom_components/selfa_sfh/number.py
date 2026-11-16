"""Documented physical values, with bounded installation-specific power limits."""
from homeassistant.components.number import NumberEntity, NumberMode

from .control_entity import SelfaControlEntity
from .controls import CONTROLS


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(SelfaNumber(entry.runtime_data, c) for c in CONTROLS if c.kind == "number")


class SelfaNumber(SelfaControlEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, control):
        super().__init__(coordinator, control)
        self._attr_native_step = control.step
        self._attr_native_unit_of_measurement = control.unit

    @property
    def native_min_value(self):
        c = self.control
        return max(c.minimum, -self.coordinator.power_limit) if c.power and c.signed else c.minimum

    @property
    def native_max_value(self):
        return min(self.control.maximum, self.coordinator.power_limit) if self.control.power else self.control.maximum

    @property
    def native_value(self):
        return self.control_value()

    async def async_set_native_value(self, value):
        await self.write(value)
