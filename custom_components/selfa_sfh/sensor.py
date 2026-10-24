"""All documented values plus human-readable operating status."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import BATTERY_STATES, WORK_STATES
from .entity import SelfaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(
        [SelfaRegisterSensor(coordinator, reg) for reg in coordinator.registers]
        + [
            SelfaStateSensor(coordinator, "working_status", "working_status_raw", WORK_STATES),
            SelfaStateSensor(coordinator, "battery_mode", "battery_mode_raw", BATTERY_STATES),
        ]
    )


class SelfaRegisterSensor(SelfaEntity, SensorEntity):
    """A typed, scaled register. Native Python integers preserve all flag bits."""

    def __init__(self, coordinator, register) -> None:
        super().__init__(coordinator, register.key)
        self.register = register
        self._attr_native_unit_of_measurement = register.unit
        self._attr_device_class = register.device_class
        self._attr_state_class = register.state_class
        if register.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if register.data_type != "STR":
            self._attr_suggested_display_precision = {1: 0, 10: 1, 100: 2, 1000: 3}[
                register.divisor
            ]

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.key)

    @property
    def extra_state_attributes(self):
        reg = self.register
        attrs = {
            **super().extra_state_attributes,
            "register": reg.address,
            "data_type": reg.data_type,
            "divisor": reg.divisor,
        }
        value = self.native_value
        if reg.data_type == "U32" and reg.unit is None and isinstance(value, int):
            attrs["hex"] = f"0x{value:08X}"
        if reg.key.startswith("rtc_") and isinstance(value, int):
            attrs.update(high_byte=value >> 8, low_byte=value & 255)
        if (
            53007 <= reg.address <= 53048
            and (reg.address - 53007) % 7 in (5, 6)
            and isinstance(value, int)
        ):
            attrs["time"] = f"{value >> 8:02d}:{value & 255:02d}"
        return attrs


class SelfaStateSensor(SelfaEntity, SensorEntity):
    """Status comes from the explicit register, not an assumed current sign."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, key, source, states) -> None:
        super().__init__(coordinator, key)
        self.source, self.states = source, states
        self._attr_options = [*states.values(), "other"]

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and (self.coordinator.data or {}).get(self.source) is not None
        )

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self.source)
        return self.states.get(value, "other") if value is not None else None
