"""Network/inverter availability visible as a diagnostic entity."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import EntityCategory

from .entity import SelfaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SelfaConnectionSensor(entry.runtime_data, "connection")])


class SelfaConnectionSensor(SelfaEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.last_update_success
