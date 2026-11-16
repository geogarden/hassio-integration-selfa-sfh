"""Confirmed writes against a local Modbus server; no physical inverter."""
import asyncio
from datetime import time
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.selfa_sfh.controls import BY_KEY, CONTROLS, validate_period
from custom_components.selfa_sfh.coordinator import SelfahybridCoordinator
from custom_components.selfa_sfh.faults import fault_attributes
from custom_components.selfa_sfh.registers import load_registers
from tests.conftest import make_entry
from tests.test_selfa import client


def test_allowlist_and_physical_encoding():
    assert len(BY_KEY) == len(CONTROLS)
    addresses = {r.address for r in load_registers()}
    assert {c.address for c in CONTROLS} <= addresses
    assert not {c.address for c in CONTROLS} & set(range(53500, 53524))
    assert BY_KEY['operating_mode'].encode('economic') == 0x0102
    assert BY_KEY['on_grid_end_soc'].encode(25.5) == 255
    assert BY_KEY['on_grid_end_soc'].decode(255) == 25.5
    assert BY_KEY['battery_target'].encode(-1.23) == 65536 - 123
    assert BY_KEY['battery_target'].decode(65536 - 123) == -1.23
    assert BY_KEY['period_1_start'].encode(time(23, 59)) == 0x173B
    for value in (float('nan'), float('inf'), -0.1, 100.1, 22.55):
        with pytest.raises(ValueError):
            BY_KEY['on_grid_end_soc'].encode(value)
    with pytest.raises(ValueError):
        BY_KEY['power_factor'].encode(0)
    with pytest.raises(ValueError):
        BY_KEY['period_1_start'].encode(time(1, 2, 3))
    with pytest.raises(ValueError):
        validate_period(0x1800, 0x0100)
    validate_period(0x1700, 0x0100)  # Overnight periods are valid.


def test_diagnostics_preserve_unknown_flags():
    data = fault_attributes('fault_flag1', 1 | (1 << 31))
    assert data['active_faults'][0] == 'Brak sieci'
    assert data['unknown_bits'] == [31]
    assert fault_attributes('bms_error_code', 1)['unknown_bits'] == [0]


async def prepared(hass, gateway, options=None):
    regs = load_registers()
    for reg in regs:
        for a in range(reg.address, reg.address + reg.count):
            gateway.words.setdefault(a, 0)
    gateway.words[10105] = 2
    bus = client(gateway)
    coord = SelfahybridCoordinator(hass, make_entry(gateway, options=options), bus, regs)
    coord.async_set_updated_data(await coord._async_update_data())
    return coord, bus


@pytest.mark.asyncio
async def test_mode_and_numeric_confirmation(hass, gateway):
    coord, bus = await prepared(hass, gateway)
    try:
        assert all(r[0] == 3 for r in gateway.requests)  # Loading never writes.
        await coord.async_set_control('operating_mode', 'economic')
        assert gateway.words[50000] == 0x0102
        await coord.async_set_control('on_grid_end_soc', 25.5)
        assert gateway.words[52503] == 255
        gateway.reject_writes = True
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('on_grid_end_soc', 30)
        assert coord.control_raw(52503) == 255
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('anything', 1)
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_mask_is_fresh_and_concurrent_changes_preserve_bits(hass, gateway):
    coord, bus = await prepared(hass, gateway)
    for slot in range(6):
        gateway.words[53012 + slot*7] = 0x0100
        gateway.words[53013 + slot*7] = 0x0200
    gateway.words[53006] = 0x8000  # Reserved bit must survive.
    try:
        await asyncio.gather(coord.async_set_control('period_1_enabled', True),
                             coord.async_set_control('period_2_enabled', True))
        assert gateway.words[53006] == 0x8003
        with pytest.raises(HomeAssistantError, match='Disable this period'):
            await coord.async_set_control('period_1_start', time(3, 0))
        await coord.async_set_control('period_1_enabled', False)
        await coord.async_set_control('period_1_start', time(23, 59))
        assert gateway.words[53012] == 0x173B
        assert gateway.words[53006] == 0x8002
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_service_and_ems_gates_and_power_ceiling(hass, gateway):
    coord, bus = await prepared(hass, gateway)
    try:
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('operating_mode', 'ems_battery')
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('ac_target', 1)
        with pytest.raises(HomeAssistantError):
            await coord.async_wo_command('off_grid_on')
        coord.service_controls = coord.ems_controls = True
        coord.power_limit = 8
        await coord.async_set_control('battery_target', -2.65)
        assert gateway.words[50207] == 65536 - 265
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('battery_target', 8.01)
        await coord.async_set_control('operating_mode', 'ems_battery')
        assert gateway.words[50000] == 0x0303
        with patch.object(coord, 'async_request_refresh', new_callable=AsyncMock):
            gateway.requests.clear()
            await coord.async_wo_command('clear_off_grid_overload')
            assert gateway.requests == [(6, 50201, 1, 247)]
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_clock_confirmed_and_no_automatic_sync(hass, gateway):
    coord, bus = await prepared(hass, gateway)
    try:
        assert not any(r[0] == 6 for r in gateway.requests)
        await coord.async_sync_clock()
        assert gateway.words[20000] >> 8 == 26
        assert 1 <= gateway.words[20000] & 255 <= 12
        assert gateway.words[20002] >> 8 < 60
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_invalid_period_never_enables_or_touches_reserved_bits(hass, gateway):
    coord, bus = await prepared(hass, gateway)
    gateway.words[53006] = 0xC000
    gateway.words[53012] = gateway.words[53013] = 0
    try:
        gateway.requests.clear()
        with pytest.raises(HomeAssistantError):
            await coord.async_set_control('period_1_enabled', True)
        assert gateway.words[53006] == 0xC000
        assert not any(req[0] == 6 for req in gateway.requests)
    finally:
        await bus.disconnect()


def test_all_controls_have_names_and_translated_enum_states():
    import json
    from pathlib import Path
    root = Path(__file__).parents[1] / 'custom_components/selfa_sfh'
    for path in ('strings.json', 'translations/en.json', 'translations/pl.json'):
        catalog = json.loads((root / path).read_text())
        for control in CONTROLS:
            item = catalog['entity'][control.kind][control.key]
            assert item['name'].strip()
            if control.kind == 'select':
                assert set(item['state']) == {key for key, _ in control.choices}
