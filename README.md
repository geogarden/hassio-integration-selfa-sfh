# Selfa SFH Hybrid Inverter — Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

Full monitoring and control of the **Selfa SFH hybrid inverter** directly from Home Assistant via **Modbus TCP/RTU**.

> Based on the *Selfa Hybrid Inverter MODBUS RTU Protocol* document (Version 1.4).

---

## Features

- **50+ sensors** — grid voltages/currents, PV string data, battery state, energy counters (daily & total), temperatures, BMS cell data, backup/EPS port
- **2 switches** — Grid Injection Limit, Off-Grid Function
- **1 select** — Inverter Working Mode (General / Economic / UPS / Off-Grid / EMS modes)
- **1 number slider** — Grid Injection Power Limit (%)
- Efficient grouped Modbus reads (minimises traffic)
- Auto-reconnect on connection loss
- HACS-compatible

---

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**
2. Add this repository URL, category: **Integration**
3. Search for **Selfa SFH** and install
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/selfa_sfh` folder into `config/custom_components/`
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Selfa SFH**
3. Fill in the connection details:

| Field | Default | Description |
|-------|---------|-------------|
| Host | — | IP address of the inverter |
| Port | `502` | Modbus TCP port |
| Slave ID | `1` | Modbus device ID |
| Protocol | `tcp` | `tcp`, `rtu_over_tcp`, or `udp` |
| Scan interval | `30` | Polling interval in seconds |

---

## Entities

### Sensors

| Entity | Unit | Description |
|--------|------|-------------|
| Inverter Working Status | — | Current operating state |
| Grid Power (3-Phase Meter) | kW | Total power at grid meter |
| Grid Power Phase A/B/C | kW | Per-phase grid power |
| Inverter AC Power | kW | Total inverter AC output |
| Phase A/B/C Voltage | V | Grid phase voltages |
| AB/BC/CA Line Voltage | V | Line-to-line voltages |
| Phase A/B/C Current | A | Grid currents |
| Grid Frequency | Hz | Measured grid frequency |
| Energy Today | kWh | Daily inverter generation |
| Daily PV Generation | kWh | Daily solar harvest |
| Daily Energy Injected to Grid | kWh | Daily export |
| Daily Energy Purchased from Grid | kWh | Daily import |
| Daily Battery Charging/Discharging | kWh | Daily battery flows |
| Daily Load Consumption | kWh | Daily household consumption |
| Total Energy Generated | kWh | Lifetime generation |
| Total PV Generation | kWh | Lifetime PV harvest |
| Total Injected/Purchased | kWh | Lifetime grid exchange |
| Total Battery Charging/Discharging | kWh | Lifetime battery flows |
| Total Load Consumption | kWh | Lifetime load |
| Total Generation Hours | h | Runtime hours |
| PV1/PV2 Voltage | V | String voltages |
| PV1/PV2 Current | A | String currents |
| PV1/PV2 Input Power | kW | String power |
| Battery Voltage | V | DC battery voltage |
| Battery Current | A | Battery current (+ charge) |
| Battery Power | kW | Battery power flow |
| Battery Mode | — | Charging / Discharging |
| Battery State of Charge | % | SOC |
| Battery State of Health | % | SOH |
| BMS Pack Temperature | °C | Battery pack temp |
| Max/Min Cell Temperature | °C | Extreme cell temps |
| Max/Min Cell Voltage | V | Extreme cell voltages |
| Inverter Temperature 1–4 | °C | Internal temperatures |
| Backup Phase A/B/C Power | kW | EPS port power |
| Backup Total Power | kW | Total EPS power |
| Smart Meter Status | — | Meter comms status |

### Switches

| Entity | Description |
|--------|-------------|
| Grid Injection Power Limit | Enable/disable the export power cap |
| Off-Grid Function | Enable/disable off-grid (EPS) mode |

### Select

| Entity | Options |
|--------|---------|
| Inverter Working Mode | General, Economic, UPS, Off-Grid, EMS AC Control, EMS General, EMS Battery Control, EMS Off-Grid |

### Number

| Entity | Range | Description |
|--------|-------|-------------|
| Grid Injection Power Limit | 0–100 % | Maximum allowed export percentage |

---

## Modbus Register Reference

Key registers used (from the official Selfa SFH Modbus RTU Protocol document):

| Register | Address | Description |
|----------|---------|-------------|
| Working Status | 0x000B | Inverter state |
| P-meter 3-phase | 0x0016–0x0017 | Grid power (I32, ×10 kW) |
| Phase A Voltage | 0x001F | V (×10) |
| Grid Frequency | 0x0025 | Hz (×100) |
| Battery Voltage | 0x0057 | V (×10) |
| SOC | 0x009F | % |
| Working Mode | 0xC350 | RW – mode select |
| Grid Inj. Switch | 0x0076 | RW – on/off |
| Grid Inj. Limit | 0x0077 | RW – % |

---

## Troubleshooting

**"Cannot connect"** — Verify the IP is reachable, port 502 is not firewalled, and the Slave ID matches the inverter setting (check the inverter's LCD/app).

**Sensors show "Unknown"** — Some registers may not be present on all firmware versions. This is normal.

**Protocol selection** — Most Selfa SFH units work with plain `tcp`. Try `rtu_over_tcp` if you get consistent read errors.

---

## Requirements

- Home Assistant 2024.1+
- `pymodbus >= 3.5.0` (auto-installed)
- Network access to the inverter (Modbus TCP on port 502 by default)

---

## License

MIT — see [LICENSE](LICENSE)
