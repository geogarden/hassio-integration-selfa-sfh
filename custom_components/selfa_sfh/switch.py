"""Documented switches and individual schedule enable bits, with readback."""
from homeassistant.components.switch import SwitchEntity

from .control_entity import SelfaControlEntity
from .controls import BY_KEY, CONTROLS


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(SelfaSwitch(entry.runtime_data, c.key) for c in CONTROLS if c.kind == "switch")


class SelfaSwitch(SelfaControlEntity, SwitchEntity):
    def __init__(self, coordinator, key):
        super().__init__(coordinator, BY_KEY[key])

    @property
    def is_on(self):
        return self.control_value()

    async def async_turn_on(self, **kwargs):
        await self.write(True)

    async def async_turn_off(self, **kwargs):
        await self.write(False)
