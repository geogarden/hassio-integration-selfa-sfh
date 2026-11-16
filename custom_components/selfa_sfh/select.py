"""Operating modes and documented enumerated settings."""
from homeassistant.components.select import SelectEntity

from .control_entity import SelfaControlEntity
from .controls import CONTROLS


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(SelfaSelect(entry.runtime_data, c) for c in CONTROLS if c.kind == "select")


class SelfaSelect(SelfaControlEntity, SelectEntity):
    def __init__(self, coordinator, control):
        super().__init__(coordinator, control)
        self._attr_options = [label for label, _ in control.choices]

    @property
    def current_option(self):
        return self.control_value()

    async def async_select_option(self, option):
        await self.write(option)
