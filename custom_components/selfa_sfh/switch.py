"""The two 0/1 controls from the ESPHome configuration, with readback."""

from homeassistant.components.switch import SwitchEntity

from .const import CONTROL_REGISTERS
from .entity import SelfaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(SelfaSwitch(entry.runtime_data, key) for key in CONTROL_REGISTERS)


class SelfaSwitch(SelfaEntity, SwitchEntity):
    """Never change the displayed switch until the inverter confirms its state."""

    @property
    def is_on(self):
        value = (self.coordinator.data or {}).get(self.key)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_switch(self.key, True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_switch(self.key, False)
