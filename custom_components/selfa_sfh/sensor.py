"""Sensor platform for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SelfahybridCoordinator


@dataclass
class SelfahybridSensorDescription(SensorEntityDescription):
    """Describes a Selfa SFH sensor."""
    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[SelfahybridSensorDescription, ...] = (
    # ── Inverter Status ─────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="working_status",
        data_key="working_status",
        name="Inverter Working Status",
        icon="mdi:solar-power",
    ),
    # ── Grid / AC Power ────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="pmeter_3ph",
        data_key="pmeter_3ph",
        name="Grid Power (3-Phase Meter)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pmeter_a",
        data_key="pmeter_a",
        name="Grid Power Phase A",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pmeter_b",
        data_key="pmeter_b",
        name="Grid Power Phase B",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pmeter_c",
        data_key="pmeter_c",
        name="Grid Power Phase C",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="p_ac",
        data_key="p_ac",
        name="Inverter AC Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Grid Voltages ───────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="phase_a_v",
        data_key="phase_a_v",
        name="Phase A Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="phase_b_v",
        data_key="phase_b_v",
        name="Phase B Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="phase_c_v",
        data_key="phase_c_v",
        name="Phase C Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="ab_line_v",
        data_key="ab_line_v",
        name="AB Line Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="bc_line_v",
        data_key="bc_line_v",
        name="BC Line Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="ca_line_v",
        data_key="ca_line_v",
        name="CA Line Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Grid Currents ───────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="phase_a_i",
        data_key="phase_a_i",
        name="Phase A Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="phase_b_i",
        data_key="phase_b_i",
        name="Phase B Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="phase_c_i",
        data_key="phase_c_i",
        name="Phase C Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Grid Frequency ──────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="grid_freq",
        data_key="grid_freq",
        name="Grid Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Energy (daily) ──────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="energy_today",
        data_key="energy_today",
        name="Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_pv_gen",
        data_key="daily_pv_gen",
        name="Daily PV Generation",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_inj",
        data_key="daily_inj",
        name="Daily Energy Injected to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_purch",
        data_key="daily_purch",
        name="Daily Energy Purchased from Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_bat_chg",
        data_key="daily_bat_chg",
        name="Daily Battery Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_bat_dchg",
        data_key="daily_bat_dchg",
        name="Daily Battery Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_load",
        data_key="daily_load",
        name="Daily Load Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="daily_backup",
        data_key="daily_backup",
        name="Daily Energy on Backup Port",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # ── Energy (total) ──────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="energy_total",
        data_key="energy_total",
        name="Total Energy Generated",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_pv_gen",
        data_key="total_pv_gen",
        name="Total PV Generation",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_inj",
        data_key="total_inj",
        name="Total Energy Injected to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_purch_grid",
        data_key="total_purch_grid",
        name="Total Energy Purchased from Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_bat_chg",
        data_key="total_bat_chg",
        name="Total Battery Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_bat_dchg",
        data_key="total_bat_dchg",
        name="Total Battery Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_load",
        data_key="total_load",
        name="Total Load Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SelfahybridSensorDescription(
        key="total_gen_h",
        data_key="total_gen_h",
        name="Total Generation Hours",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:clock-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # ── PV Strings ──────────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="pv1_v",
        data_key="pv1_v",
        name="PV1 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pv1_i",
        data_key="pv1_i",
        name="PV1 Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pv1_p",
        data_key="pv1_p",
        name="PV1 Input Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pv2_v",
        data_key="pv2_v",
        name="PV2 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pv2_i",
        data_key="pv2_i",
        name="PV2 Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="pv2_p",
        data_key="pv2_p",
        name="PV2 Input Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Battery ─────────────────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="battery_v",
        data_key="battery_v",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="battery_i",
        data_key="battery_i",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="battery_p",
        data_key="battery_p",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="battery_mode",
        data_key="battery_mode",
        name="Battery Mode",
        icon="mdi:battery-charging",
    ),
    SelfahybridSensorDescription(
        key="soc",
        data_key="soc",
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="soh",
        data_key="soh",
        name="Battery State of Health",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-heart-variant",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="bms_pack_temp",
        data_key="bms_pack_temp",
        name="BMS Pack Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="max_cell_temp",
        data_key="max_cell_temp",
        name="Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="min_cell_temp",
        data_key="min_cell_temp",
        name="Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="max_cell_v",
        data_key="max_cell_v",
        name="Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="min_cell_v",
        data_key="min_cell_v",
        name="Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Temperatures (Inverter) ─────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="temp1",
        data_key="temp1",
        name="Inverter Temperature 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="temp2",
        data_key="temp2",
        name="Inverter Temperature 2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="temp3",
        data_key="temp3",
        name="Inverter Temperature 3",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="temp4",
        data_key="temp4",
        name="Inverter Temperature 4",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Backup (EPS) Port ───────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="backup_a_v",
        data_key="backup_a_v",
        name="Backup Phase A Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="backup_a_i",
        data_key="backup_a_i",
        name="Backup Phase A Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="backup_a_p",
        data_key="backup_a_p",
        name="Backup Phase A Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="backup_b_p",
        data_key="backup_b_p",
        name="Backup Phase B Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="backup_c_p",
        data_key="backup_c_p",
        name="Backup Phase C Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SelfahybridSensorDescription(
        key="backup_total_p",
        data_key="backup_total_p",
        name="Backup Total Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Smart meter status ──────────────────────────────────────────────────
    SelfahybridSensorDescription(
        key="smart_meter_normal",
        data_key="smart_meter_normal",
        name="Smart Meter Status",
        icon="mdi:meter-electric",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Selfa SFH sensors from a config entry."""
    coordinator: SelfahybridCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SelfahybridSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SelfahybridSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Selfa SFH sensor."""

    entity_description: SelfahybridSensorDescription

    def __init__(
        self,
        coordinator: SelfahybridCoordinator,
        description: SelfahybridSensorDescription,
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

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self.entity_description.data_key)
        if isinstance(val, bool):
            return "Normal" if val else "Abnormal"
        return val
