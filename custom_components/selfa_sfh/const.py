"""Constants for the Selfa SFH Hybrid Inverter integration."""

DOMAIN = "selfa_sfh"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PROTOCOL = "tcp"

PROTOCOLS = ["tcp", "rtu_over_tcp", "udp"]

CONF_SLAVE_ID = "slave_id"
CONF_PROTOCOL = "protocol"
CONF_SCAN_INTERVAL = "scan_interval"

# ─────────────────────────────────────────────
# Read-Only Registers (Function Code 0x03)
# Addresses from the Selfa SFH Modbus RTU Protocol document
# ─────────────────────────────────────────────

# Device Info
REG_DEVICE_SN          = 0x0000   # Device SN (string, read by bytes)
REG_INVERTER_MODEL     = 0x0002   # Inverter Model (U16)
REG_FIRMWARE_VERSION   = 0x0003   # Firmware Version (U16)
REG_DATE_YM            = 0x0004   # Date Year/Month (U16)
REG_TIME_DH            = 0x0005   # Time Day/Hour (U16)
REG_TIME_MS            = 0x0006   # Time Min/Sec (U16)
REG_SAFETY_CODE        = 0x0007   # Safety Code (U16)

# Inverter Working Status
REG_WORKING_STATUS     = 0x000B   # Inverter Working Status (U16)
REG_FAULT_FLAG1        = 0x000D   # Fault FLAG 1 (U16)
REG_FAULT_FLAG2        = 0x000E   # Fault FLAG 2 (U16)
REG_FAULT_FLAG3        = 0x000F   # Fault FLAG 3 (U16)

# AC measurements
REG_PMETER_A           = 0x0010   # P-meter on Phase A (I32, kW, ×10)
REG_PMETER_B           = 0x0012   # P-meter on Phase B (I32, kW, ×10)
REG_PMETER_C           = 0x0014   # P-meter on Phase C (I32, kW, ×10)
REG_PMETER_3PH         = 0x0016   # P-meter of three phases (I32, kW, ×10)
REG_TOTAL_GRID_INJ     = 0x0018   # Total Grid Injection Energy on Meter (U32, kWh, ×10)
REG_TOTAL_PURCHASING   = 0x001A   # Total Purchasing Energy from Grid on Meter (U32, kWh, ×10)

REG_AB_LINE_VOLTAGE    = 0x001C   # AB line voltage (U16, V, ×10)
REG_BC_LINE_VOLTAGE    = 0x001D   # BC line voltage (U16, V, ×10)
REG_CA_LINE_VOLTAGE    = 0x001E   # CA line voltage (U16, V, ×10)
REG_PHASE_A_VOLTAGE    = 0x001F   # Phase A Voltage (U16, V, ×10)
REG_PHASE_A_CURRENT    = 0x0020   # Phase A Current (U16, A, ×10)
REG_PHASE_B_VOLTAGE    = 0x0021   # Phase B Voltage (U16, V, ×10)
REG_PHASE_B_CURRENT    = 0x0022   # Phase B Current (U16, A, ×10)
REG_PHASE_C_VOLTAGE    = 0x0023   # Phase C Voltage (U16, V, ×10)
REG_PHASE_C_CURRENT    = 0x0024   # Phase C Current (U16, A, ×10)
REG_GRID_FREQUENCY     = 0x0025   # Grid Frequency (U16, Hz, ×100)
REG_P_AC               = 0x0026   # P_AC (I32, kW, ×10)
REG_ENERGY_TODAY       = 0x0028   # Energy today (U32, kWh, ×10)
REG_ENERGY_TOTAL       = 0x002A   # Energy total (U32, kWh, ×10)
REG_TOTAL_GEN_HOURS    = 0x002C   # Total Generation Hours (U32, h, ×10)
REG_TOTAL_PV_INPUT     = 0x002E   # Total PV Input Power (U32, kW, ×10)

# Temperature sensors
REG_TEMP1              = 0x0030   # Temp 1 (I16, °C, ×10)
REG_TEMP2              = 0x0031   # Temp 2 (I16, °C, ×10)
REG_TEMP3              = 0x0032   # Temp 3 (I16, °C, ×10)
REG_TEMP4              = 0x0033   # Temp 4 (I16, °C, ×10)

# PV strings
REG_PV1_VOLTAGE        = 0x0034   # PV1 Voltage (U16, V, ×10)
REG_PV1_CURRENT        = 0x0035   # PV1 Current (U16, A, ×10)
REG_PV2_VOLTAGE        = 0x0036   # PV2 Voltage (U16, V, ×10)
REG_PV2_CURRENT        = 0x0037   # PV2 Current (U16, A, ×10)
REG_PV_INPUT_POWER1    = 0x0038   # PV Input Power 1 (U32, kW, ×10)
REG_PV_INPUT_POWER2    = 0x003A   # PV Input Power 2 (U32, kW, ×10)

# ARM Fault
REG_ARM_FAULT_FLAG     = 0x003C   # ARM Fault FLAG (U16)

# Backup/EPS measurements
REG_BACKUP_A_V         = 0x0040   # Backup A Voltage (U16, V, ×10)
REG_BACKUP_A_I         = 0x0041   # Backup A Current (U16, A, ×10)
REG_BACKUP_A_F         = 0x0042   # Backup A Frequency (U16, Hz, ×100)
REG_BACKUP_A_P         = 0x0043   # Backup A Active Power (I32, kW, ×10)
REG_BACKUP_B_V         = 0x0045   # Backup B Voltage (U16, V, ×10)
REG_BACKUP_B_I         = 0x0046   # Backup B Current (U16, A, ×10)
REG_BACKUP_B_F         = 0x0047   # Backup B Frequency (U16, Hz, ×100)
REG_BACKUP_B_P         = 0x0048   # Backup B Active Power (I32, kW, ×10)
REG_BACKUP_C_V         = 0x004A   # Backup C Voltage (U16, V, ×10)
REG_BACKUP_C_I         = 0x004B   # Backup C Current (U16, A, ×10)
REG_BACKUP_C_F         = 0x004C   # Backup C Frequency (U16, Hz, ×100)
REG_BACKUP_C_P         = 0x004D   # Backup C Active Power (I32, kW, ×10)
REG_TOTAL_BACKUP_P     = 0x004F   # Total Backup Active Power (I32, kW, ×10)
REG_INVT_A_P           = 0x0051   # Inverter Phase A Active Power (I32, kW, ×10)
REG_INVT_B_P           = 0x0053   # Inverter Phase B Active Power (I32, kW, ×10)
REG_INVT_C_P           = 0x0055   # Inverter Phase C Active Power (I32, kW, ×10)

# Battery
REG_BATTERY_V          = 0x0057   # Battery Voltage (U16, V, ×10)
REG_BATTERY_I          = 0x0058   # Battery Current (I16, A, ×10)
REG_BATTERY_MODE       = 0x0059   # Battery Mode (U16, 0=discharge/1=charge)
REG_BATTERY_P          = 0x005A   # Battery Power (I32, kW, ×10)

# Daily energy counters
REG_DAILY_INJ          = 0x0060   # Daily Energy Injected to Grid (U16, kWh, ×10)
REG_DAILY_PURCH        = 0x0061   # Daily Purchased Energy (U16, kWh, ×10)
REG_DAILY_BACKUP       = 0x0062   # Daily Energy Output on Backup Port (U16, kWh, ×10)
REG_DAILY_BAT_CHG      = 0x0063   # Daily Battery Charging Energy (U16, kWh, ×10)
REG_DAILY_BAT_DCHG     = 0x0064   # Daily Battery Discharging Energy (U16, kWh, ×10)
REG_DAILY_PV_GEN       = 0x0065   # Daily PV Generation (U16, kWh, ×10)
REG_DAILY_LOAD         = 0x0066   # Daily Load Consumption (U16, kWh, ×10)
REG_DAILY_PURCH_INV    = 0x0067   # Daily Energy Purchased from Grid at Inverter Side (U16, kWh, ×10)

# Total energy counters (U32, kWh, ×10)
REG_TOTAL_INJ          = 0x0088   # Total Energy Injected into Grid
REG_TOTAL_PURCH_GRID   = 0x008A   # Total Purchased Energy from Grid
REG_TOTAL_BACKUP       = 0x008C   # Total Output Energy on Backup Port
REG_TOTAL_BAT_CHG      = 0x008E   # Total Battery Charging Energy
REG_TOTAL_BAT_DCHG     = 0x0090   # Total Battery Discharging Energy
REG_TOTAL_PV_GEN       = 0x0092   # Total PV Generation
REG_TOTAL_LOAD         = 0x0094   # Total Load Consumption
REG_TOTAL_PURCH_INV    = 0x0096   # Total Energy Purchased from Grid at Inverter Side

# Battery type / BMS info
REG_BATTERY_TYPE_CODES = 0x0098   # Battery Type Codes (U16)
REG_BATTERY_STRINGS    = 0x0099   # Battery Strings (U16)
REG_BATTERY_PROTOCOL   = 0x009A   # Battery Protocol (U16)
REG_SOFTWARE_VERSION   = 0x009B   # Software Version (U16)
REG_HARDWARE_VERSION   = 0x009C   # Hardware Version (U16)
REG_BMS_CHARGE_IMAX    = 0x009D   # BMS Charge Imax (U16, A, ×10)
REG_BMS_DCHG_IMAX      = 0x009E   # BMS Discharge Imax (U16, A, ×10)
REG_SOC                = 0x009F   # SOC (U16, %)
REG_SOH                = 0x00A0   # SOH (U16, %)
REG_BMS_STATUS         = 0x00A1   # BMS Status (U16)
REG_BMS_PACK_TEMP      = 0x00A2   # BMS Pack Temperature (I16, °C, ×10)
REG_MAX_CELL_TEMP_ID   = 0x00A3   # Max Cell Temperature ID (U16)
REG_MAX_CELL_TEMP      = 0x00A4   # Max Cell Temperature (I16, °C, ×10)
REG_MIN_CELL_TEMP_ID   = 0x00A5   # Min Cell Temperature ID (U16)
REG_MIN_CELL_TEMP      = 0x00A6   # Min Cell Temperature (I16, °C, ×10)
REG_MAX_CELL_V_ID      = 0x00A7   # Max Cell Voltage ID (U16)
REG_MAX_CELL_V         = 0x00A8   # Max Cell Voltage (U16, V, ×1000)
REG_MIN_CELL_V_ID      = 0x00A9   # Min Cell Voltage ID (U16)
REG_MIN_CELL_V         = 0x00AA   # Min Cell Voltage (U16, V, ×1000)
REG_BMS_ERROR_CODE     = 0x00AB   # BMS Error Code (U16)
REG_BMS_WARN_CODE      = 0x00AC   # BMS Warn Code (U16)

# ─────────────────────────────────────────────
# Read/Write Registers (Function Code 0x03/0x06)
# ─────────────────────────────────────────────
REG_RTC_DATE_TIME1     = 0x0071   # RTC Year/Month
REG_RTC_DATE_TIME2     = 0x0072   # RTC Day/Hour
REG_RTC_DATE_TIME3     = 0x0073   # RTC Min/Sec
REG_RW_SAFETY_CODE     = 0x0074   # Safety Code (RW)
REG_OVERLOAD_METHOD    = 0x0075   # Overload Method Setting
REG_GRID_INJ_SWITCH    = 0x0076   # Grid Injection Power Limit Switch (0=OFF, 1=ON)
REG_GRID_INJ_LIMIT     = 0x0077   # Grid Injection Power Limit Setting
REG_SMART_METER_STATUS = 0x0078   # Smart Meter COM Status (0=abnormal, 1=normal)

# Power scheduling (EMS)
REG_WORKING_MODE       = 0xC350   # Hybrid Inverter Working Mode Setting (50000)
REG_EMS_AC_CTRL_TOTAL  = 0xC4CA   # EMS AC Ctrl: Total Power Scheduling Setting (50378)
REG_EMS_AC_CTRL_A      = 0xC4CB   # EMS AC Ctrl: Phase A Power Scheduling Setting
REG_EMS_AC_CTRL_B      = 0xC4CC   # EMS AC Ctrl: Phase B Power Scheduling Setting
REG_EMS_AC_CTRL_C      = 0xC4CD   # EMS AC Ctrl: Phase C Power Scheduling Setting
REG_EMS_GENERAL_MODE   = 0xC4CE   # EMS General Mode (50382)
REG_EMS_BATT_CHG       = 0xC4CF   # EMS Batt Ctrl: Battery Charge Set Pbat
REG_EMS_BATT_DCHG      = 0xC4D3   # EMS Batt Ctrl: Battery Discharge Set Pbat
REG_EMS_OFF_GRID_MODE  = 0xC4D3   # EMS Off-Grid Mode PV Power Scheduling (50211)

# ─────────────────────────────────────────────
# Write-Only Registers
# ─────────────────────────────────────────────
REG_OFF_GRID_FUNCTION  = 0xC3D2   # Off-grid function switch (50130, WO)
REG_CLEAR_OFF_GRID_OVL = 0xC3D3   # Clear off-grid overloading protection flag

# ─────────────────────────────────────────────
# Working Mode values (REG_WORKING_MODE)
# ─────────────────────────────────────────────
WORKING_MODE_GENERAL   = 0x0000
WORKING_MODE_ECONOMIC  = 0x0001
WORKING_MODE_UPS       = 0x0002
WORKING_MODE_OFF_GRID  = 0x0003
WORKING_MODE_EMS_ACC   = 0x0101
WORKING_MODE_EMS_GEN   = 0x0102
WORKING_MODE_EMS_BAT   = 0x0103
WORKING_MODE_EMS_OFF   = 0x0104

WORKING_MODE_OPTIONS = {
    "General Mode": WORKING_MODE_GENERAL,
    "Economic Mode": WORKING_MODE_ECONOMIC,
    "UPS Mode": WORKING_MODE_UPS,
    "Off-Grid Mode": WORKING_MODE_OFF_GRID,
    "EMS AC Control Mode": WORKING_MODE_EMS_ACC,
    "EMS General Mode": WORKING_MODE_EMS_GEN,
    "EMS Battery Control Mode": WORKING_MODE_EMS_BAT,
    "EMS Off-Grid Mode": WORKING_MODE_EMS_OFF,
}

# Battery mode values
BATTERY_MODE_DISCHARGE = 0
BATTERY_MODE_CHARGE    = 1

# Inverter Working Status values
INV_STATUS_WAIT_GRID   = 0
INV_STATUS_SELFCHECK   = 1
INV_STATUS_ON_GRID     = 2
INV_STATUS_FAULT       = 3
INV_STATUS_FW_UPGRADE  = 4
INV_STATUS_OFF_GRID    = 5

INV_STATUS_MAP = {
    INV_STATUS_WAIT_GRID: "Waiting for Grid",
    INV_STATUS_SELFCHECK: "Self-Checking",
    INV_STATUS_ON_GRID:   "On-Grid Generating",
    INV_STATUS_FAULT:     "Device Fault",
    INV_STATUS_FW_UPGRADE:"Firmware Upgrade",
    INV_STATUS_OFF_GRID:  "Off-Grid Generating",
}
