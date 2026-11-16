"""Local HH:MM values packed as high-byte hours and low-byte minutes."""
from datetime import time

from homeassistant.components.time import TimeEntity

from .control_entity import SelfaControlEntity
from .controls import CONTROLS, valid_time


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(SelfaTime(entry.runtime_data, c) for c in CONTROLS if c.kind == "time")


class SelfaTime(SelfaControlEntity, TimeEntity):
    @property
    def native_value(self):
        raw = self.coordinator.control_raw(self.control.address)
        return time(raw >> 8, raw & 255) if raw is not None and valid_time(raw) else None

    async def async_set_value(self, value):
        await self.write(value)
