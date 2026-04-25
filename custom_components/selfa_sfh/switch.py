"""Switch platform for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_GRID_INJ_SWITCH, REG_OFF_GRID_FUNCTION
from .coordinator import SelfahybridCoordinator


@dataclass
class SelfahybridSwitchDescription(SwitchEntityDescription):
    data_key: str = ""
    register: int = 0
    on_value: int = 1
    off_value: int = 0


SWITCH_DESCRIPTIONS: tuple[SelfahybridSwitchDescription, ...] = (
    SelfahybridSwitchDescription(
        key="grid_inj_switch",
        data_key="grid_inj_switch",
        name="Grid Injection Power Limit",
        icon="mdi:transmission-tower-export",
        register=REG_GRID_INJ_SWITCH,
        on_value=1,
        off_value=0,
    ),
    SelfahybridSwitchDescription(
        key="off_grid_function",
        data_key=None,          # WO register, no readback
        name="Off-Grid Function",
        icon="mdi:solar-power-variant",
        register=REG_OFF_GRID_FUNCTION,
        on_value=1,
        off_value=0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SelfahybridCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SelfahybridSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    )


class SelfahybridSwitch(CoordinatorEntity, SwitchEntity):
    entity_description: SelfahybridSwitchDescription

    def __init__(
        self,
        coordinator: SelfahybridCoordinator,
        description: SelfahybridSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Selfa SFH Hybrid Inverter",
            "manufacturer": "Selfa",
            "model": "SFH",
        }
        self._assumed_state: bool | None = None

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.data_key and self.coordinator.data:
            val = self.coordinator.data.get(self.entity_description.data_key)
            if val is not None:
                return bool(val)
        return self._assumed_state

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.write_register(
            self.entity_description.register, self.entity_description.on_value
        )
        self._assumed_state = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.write_register(
            self.entity_description.register, self.entity_description.off_value
        )
        self._assumed_state = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
