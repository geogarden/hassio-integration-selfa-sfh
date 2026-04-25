"""DataUpdateCoordinator for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    INV_STATUS_MAP,
    # RO registers
    REG_WORKING_STATUS,
    REG_FAULT_FLAG1, REG_FAULT_FLAG2, REG_FAULT_FLAG3,
    REG_PMETER_A, REG_PMETER_B, REG_PMETER_C, REG_PMETER_3PH,
    REG_TOTAL_GRID_INJ, REG_TOTAL_PURCHASING,
    REG_PHASE_A_VOLTAGE, REG_PHASE_A_CURRENT,
    REG_PHASE_B_VOLTAGE, REG_PHASE_B_CURRENT,
    REG_PHASE_C_VOLTAGE, REG_PHASE_C_CURRENT,
    REG_GRID_FREQUENCY, REG_P_AC,
    REG_ENERGY_TODAY, REG_ENERGY_TOTAL,
    REG_TOTAL_GEN_HOURS, REG_TOTAL_PV_INPUT,
    REG_TEMP1, REG_TEMP2, REG_TEMP3, REG_TEMP4,
    REG_PV1_VOLTAGE, REG_PV1_CURRENT,
    REG_PV2_VOLTAGE, REG_PV2_CURRENT,
    REG_PV_INPUT_POWER1, REG_PV_INPUT_POWER2,
    REG_BACKUP_A_V, REG_BACKUP_A_I, REG_BACKUP_A_P,
    REG_BACKUP_B_V, REG_BACKUP_B_I, REG_BACKUP_B_P,
    REG_BACKUP_C_V, REG_BACKUP_C_I, REG_BACKUP_C_P,
    REG_TOTAL_BACKUP_P,
    REG_BATTERY_V, REG_BATTERY_I, REG_BATTERY_MODE, REG_BATTERY_P,
    REG_DAILY_INJ, REG_DAILY_PURCH, REG_DAILY_BACKUP,
    REG_DAILY_BAT_CHG, REG_DAILY_BAT_DCHG, REG_DAILY_PV_GEN,
    REG_DAILY_LOAD, REG_DAILY_PURCH_INV,
    REG_TOTAL_INJ, REG_TOTAL_PURCH_GRID,
    REG_TOTAL_BAT_CHG, REG_TOTAL_BAT_DCHG,
    REG_TOTAL_PV_GEN, REG_TOTAL_LOAD,
    REG_SOC, REG_SOH, REG_BMS_STATUS, REG_BMS_PACK_TEMP,
    REG_MAX_CELL_TEMP, REG_MIN_CELL_TEMP,
    REG_MAX_CELL_V, REG_MIN_CELL_V,
    REG_BMS_ERROR_CODE, REG_BMS_WARN_CODE,
    REG_ARM_FAULT_FLAG,
    REG_AB_LINE_VOLTAGE, REG_BC_LINE_VOLTAGE, REG_CA_LINE_VOLTAGE,
    # RW registers
    REG_SMART_METER_STATUS, REG_GRID_INJ_SWITCH, REG_GRID_INJ_LIMIT,
    REG_WORKING_MODE,
    BATTERY_MODE_CHARGE, BATTERY_MODE_DISCHARGE,
)
from .modbus_client import SelfahybridModbusClient

_LOGGER = logging.getLogger(__name__)


class SelfahybridCoordinator(DataUpdateCoordinator):
    """Polls the inverter and provides data to all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SelfahybridModbusClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter. Grouped reads for efficiency."""
        data: dict[str, Any] = {}

        def _r(regs: list[int] | None, index: int, default=None):
            """Safe register access."""
            if regs is None or index >= len(regs):
                return default
            return regs[index]

        def _u16(regs, i):
            v = _r(regs, i)
            return v if v is not None else None

        def _i16(regs, i):
            v = _r(regs, i)
            if v is None:
                return None
            return v if v < 0x8000 else v - 0x10000

        def _u32(regs, i):
            hi = _r(regs, i)
            lo = _r(regs, i + 1)
            if hi is None or lo is None:
                return None
            return (hi << 16) | lo

        def _i32(regs, i):
            v = _u32(regs, i)
            if v is None:
                return None
            return v if v < 0x80000000 else v - 0x100000000

        # ── Block 1: Status & Power (0x000B – 0x002F) ─────────────────────
        b1 = await self.client.read_registers(0x000B, 0x0030 - 0x000B)
        off = lambda a: a - 0x000B

        data["working_status_raw"] = _u16(b1, off(REG_WORKING_STATUS))
        data["working_status"] = INV_STATUS_MAP.get(
            data["working_status_raw"], f"Unknown ({data['working_status_raw']})"
        ) if data["working_status_raw"] is not None else None
        data["fault_flag1"] = _u16(b1, off(REG_FAULT_FLAG1))
        data["fault_flag2"] = _u16(b1, off(REG_FAULT_FLAG2))
        data["fault_flag3"] = _u16(b1, off(REG_FAULT_FLAG3))
        data["pmeter_a"]    = _div(_i32(b1, off(REG_PMETER_A)), 10)     # kW
        data["pmeter_b"]    = _div(_i32(b1, off(REG_PMETER_B)), 10)
        data["pmeter_c"]    = _div(_i32(b1, off(REG_PMETER_C)), 10)
        data["pmeter_3ph"]  = _div(_i32(b1, off(REG_PMETER_3PH)), 10)
        data["total_grid_inj"] = _div(_u32(b1, off(REG_TOTAL_GRID_INJ)), 10)   # kWh
        data["total_purchasing"] = _div(_u32(b1, off(REG_TOTAL_PURCHASING)), 10)
        data["ab_line_v"]   = _div(_u16(b1, off(REG_AB_LINE_VOLTAGE)), 10)     # V
        data["bc_line_v"]   = _div(_u16(b1, off(REG_BC_LINE_VOLTAGE)), 10)
        data["ca_line_v"]   = _div(_u16(b1, off(REG_CA_LINE_VOLTAGE)), 10)
        data["phase_a_v"]   = _div(_u16(b1, off(REG_PHASE_A_VOLTAGE)), 10)
        data["phase_a_i"]   = _div(_u16(b1, off(REG_PHASE_A_CURRENT)), 10)
        data["phase_b_v"]   = _div(_u16(b1, off(REG_PHASE_B_VOLTAGE)), 10)
        data["phase_b_i"]   = _div(_u16(b1, off(REG_PHASE_B_CURRENT)), 10)
        data["phase_c_v"]   = _div(_u16(b1, off(REG_PHASE_C_VOLTAGE)), 10)
        data["phase_c_i"]   = _div(_u16(b1, off(REG_PHASE_C_CURRENT)), 10)
        data["grid_freq"]   = _div(_u16(b1, off(REG_GRID_FREQUENCY)), 100)     # Hz
        data["p_ac"]        = _div(_i32(b1, off(REG_P_AC)), 10)
        data["energy_today"] = _div(_u32(b1, off(REG_ENERGY_TODAY)), 10)
        data["energy_total"] = _div(_u32(b1, off(REG_ENERGY_TOTAL)), 10)
        data["total_gen_h"]  = _div(_u32(b1, off(REG_TOTAL_GEN_HOURS)), 10)
        data["total_pv_input"] = _div(_u32(b1, off(REG_TOTAL_PV_INPUT)), 10)

        # ── Block 2: Temp + PV strings (0x0030 – 0x005C) ──────────────────
        b2 = await self.client.read_registers(0x0030, 0x005C - 0x0030)
        off2 = lambda a: a - 0x0030

        data["temp1"] = _div(_i16(b2, off2(REG_TEMP1)), 10)
        data["temp2"] = _div(_i16(b2, off2(REG_TEMP2)), 10)
        data["temp3"] = _div(_i16(b2, off2(REG_TEMP3)), 10)
        data["temp4"] = _div(_i16(b2, off2(REG_TEMP4)), 10)
        data["pv1_v"] = _div(_u16(b2, off2(REG_PV1_VOLTAGE)), 10)
        data["pv1_i"] = _div(_u16(b2, off2(REG_PV1_CURRENT)), 10)
        data["pv2_v"] = _div(_u16(b2, off2(REG_PV2_VOLTAGE)), 10)
        data["pv2_i"] = _div(_u16(b2, off2(REG_PV2_CURRENT)), 10)
        data["pv1_p"] = _div(_u32(b2, off2(REG_PV_INPUT_POWER1)), 10)
        data["pv2_p"] = _div(_u32(b2, off2(REG_PV_INPUT_POWER2)), 10)
        data["arm_fault_flag"] = _u16(b2, off2(REG_ARM_FAULT_FLAG))

        # ── Block 3: Backup + Battery (0x0040 – 0x0068) ───────────────────
        b3 = await self.client.read_registers(0x0040, 0x0068 - 0x0040)
        off3 = lambda a: a - 0x0040

        data["backup_a_v"] = _div(_u16(b3, off3(REG_BACKUP_A_V)), 10)
        data["backup_a_i"] = _div(_u16(b3, off3(REG_BACKUP_A_I)), 10)
        data["backup_a_p"] = _div(_i32(b3, off3(REG_BACKUP_A_P)), 10)
        data["backup_b_v"] = _div(_u16(b3, off3(REG_BACKUP_B_V)), 10)
        data["backup_b_i"] = _div(_u16(b3, off3(REG_BACKUP_B_I)), 10)
        data["backup_b_p"] = _div(_i32(b3, off3(REG_BACKUP_B_P)), 10)
        data["backup_c_v"] = _div(_u16(b3, off3(REG_BACKUP_C_V)), 10)
        data["backup_c_i"] = _div(_u16(b3, off3(REG_BACKUP_C_I)), 10)
        data["backup_c_p"] = _div(_i32(b3, off3(REG_BACKUP_C_P)), 10)
        data["backup_total_p"] = _div(_i32(b3, off3(REG_TOTAL_BACKUP_P)), 10)
        data["battery_v"]  = _div(_u16(b3, off3(REG_BATTERY_V)), 10)
        data["battery_i"]  = _div(_i16(b3, off3(REG_BATTERY_I)), 10)
        bat_mode = _u16(b3, off3(REG_BATTERY_MODE))
        data["battery_mode"] = "Charging" if bat_mode == BATTERY_MODE_CHARGE else (
            "Discharging" if bat_mode == BATTERY_MODE_DISCHARGE else None
        )
        data["battery_p"]  = _div(_i32(b3, off3(REG_BATTERY_P)), 10)

        data["daily_inj"]       = _div(_u16(b3, off3(REG_DAILY_INJ)), 10)
        data["daily_purch"]     = _div(_u16(b3, off3(REG_DAILY_PURCH)), 10)
        data["daily_backup"]    = _div(_u16(b3, off3(REG_DAILY_BACKUP)), 10)
        data["daily_bat_chg"]   = _div(_u16(b3, off3(REG_DAILY_BAT_CHG)), 10)
        data["daily_bat_dchg"]  = _div(_u16(b3, off3(REG_DAILY_BAT_DCHG)), 10)
        data["daily_pv_gen"]    = _div(_u16(b3, off3(REG_DAILY_PV_GEN)), 10)
        data["daily_load"]      = _div(_u16(b3, off3(REG_DAILY_LOAD)), 10)
        data["daily_purch_inv"] = _div(_u16(b3, off3(REG_DAILY_PURCH_INV)), 10)

        # ── Block 4: Total energy counters (0x0088 – 0x0098) ──────────────
        b4 = await self.client.read_registers(0x0088, 0x0098 - 0x0088)
        off4 = lambda a: a - 0x0088

        data["total_inj"]       = _div(_u32(b4, off4(REG_TOTAL_INJ)), 10)
        data["total_purch_grid"] = _div(_u32(b4, off4(REG_TOTAL_PURCH_GRID)), 10)
        data["total_bat_chg"]   = _div(_u32(b4, off4(REG_TOTAL_BAT_CHG)), 10)
        data["total_bat_dchg"]  = _div(_u32(b4, off4(REG_TOTAL_BAT_DCHG)), 10)
        data["total_pv_gen"]    = _div(_u32(b4, off4(REG_TOTAL_PV_GEN)), 10)
        data["total_load"]      = _div(_u32(b4, off4(REG_TOTAL_LOAD)), 10)

        # ── Block 5: BMS (0x0098 – 0x00AD) ────────────────────────────────
        b5 = await self.client.read_registers(0x0098, 0x00AD - 0x0098)
        off5 = lambda a: a - 0x0098

        data["soc"]             = _u16(b5, off5(REG_SOC))
        data["soh"]             = _u16(b5, off5(REG_SOH))
        data["bms_status"]      = _u16(b5, off5(REG_BMS_STATUS))
        data["bms_pack_temp"]   = _div(_i16(b5, off5(REG_BMS_PACK_TEMP)), 10)
        data["max_cell_temp"]   = _div(_i16(b5, off5(REG_MAX_CELL_TEMP)), 10)
        data["min_cell_temp"]   = _div(_i16(b5, off5(REG_MIN_CELL_TEMP)), 10)
        data["max_cell_v"]      = _div(_u16(b5, off5(REG_MAX_CELL_V)), 1000)
        data["min_cell_v"]      = _div(_u16(b5, off5(REG_MIN_CELL_V)), 1000)
        data["bms_error_code"]  = _u16(b5, off5(REG_BMS_ERROR_CODE))
        data["bms_warn_code"]   = _u16(b5, off5(REG_BMS_WARN_CODE))

        # ── RW registers ───────────────────────────────────────────────────
        sm = await self.client.read_u16(REG_SMART_METER_STATUS)
        data["smart_meter_normal"] = bool(sm) if sm is not None else None

        gi_sw = await self.client.read_u16(REG_GRID_INJ_SWITCH)
        data["grid_inj_switch"] = bool(gi_sw) if gi_sw is not None else None

        gi_lim = await self.client.read_u16(REG_GRID_INJ_LIMIT)
        data["grid_inj_limit"] = gi_lim  # raw %

        wm = await self.client.read_u16(REG_WORKING_MODE)
        data["working_mode"] = wm

        return data


def _div(value, divisor):
    """Safe division returning a rounded float or None."""
    if value is None:
        return None
    return round(value / divisor, 2)
