"""Protocol regression tests: documented decoding, framing and partial failure."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.selfa_sfh.config_flow import connection_schema, validate_connection
from custom_components.selfa_sfh.coordinator import SelfahybridCoordinator
from custom_components.selfa_sfh.modbus_client import (
    SelfaConnectionError,
    SelfahybridModbusClient,
    SelfaRegisterError,
)
from custom_components.selfa_sfh.registers import (
    Register,
    decode_value,
    load_registers,
    read_blocks,
)
from custom_components.selfa_sfh.sensor import SelfaRegisterSensor
from custom_components.selfa_sfh.switch import SelfaSwitch
from tests.conftest import Gateway, make_entry


def client(gateway):
    return SelfahybridModbusClient(
        "127.0.0.1", gateway.port, 247, gateway.protocol, timeout=0.2, request_delay=0
    )


@pytest.mark.parametrize(
    "kind,count,words,expected",
    [
        ("U16", 1, [65535], 65535),
        ("I16", 1, [65526], -10),
        ("U32", 2, [65535, 65535], 4294967295),
        ("I32", 2, [65535, 64536], -1000),
    ],
)
def test_exact_signed_decoding(kind, count, words, expected):
    reg = Register("test", "Test", 10, count, kind)
    assert decode_value(reg, {10 + i: v for i, v in enumerate(words)}) == expected
    assert decode_value(reg, {}) is None


def test_pdf_scaling_and_coverage():
    regs = load_registers()
    assert len(regs) == 177
    assert len({r.key for r in regs}) == 177
    assert len({r.address for r in regs}) == 177
    by_addr = {r.address: r for r in regs}
    assert decode_value(by_addr[33000], {33000: 8750}) == 87.5
    assert decode_value(by_addr[11016], {11016: 0, 11017: 8123}) == 8.123
    assert decode_value(by_addr[11002], {11002: 0, 11003: 12345}) == 123.45
    assert decode_value(by_addr[11022], {11022: 0, 11023: 99}) == 99
    assert by_addr[33009].data_type == "U16"
    assert not set(range(53500, 53524)) & by_addr.keys()
    assert not {25104, 25105, 25107, 25109, 50200, 50201, 53009, 53011} & by_addr.keys()


def test_blocks_do_not_read_gaps_or_split_values():
    for group in read_blocks(list(load_registers())):
        assert group[-1].address + group[-1].count - group[0].address <= 32
        for left, right in zip(group, group[1:]):
            assert left.address + left.count == right.address


@pytest.mark.asyncio
@pytest.mark.parametrize("protocol", ["tcp", "rtu_over_tcp"])
async def test_real_wire_framing_and_device_id(protocol):
    gw = await Gateway(protocol).start()
    bus = client(gw)
    try:
        assert await bus.read_registers(10008, 1) == [0x1E03]
        assert (
            await validate_connection(
                {"host": "127.0.0.1", "port": gw.port, "slave_id": 247, "protocol": protocol}
            )
            == "SFH1234567890123"
        )
        assert all(req[-1] == 247 for req in gw.requests)
        assert all(req[0] == 3 for req in gw.requests)
    finally:
        await bus.disconnect()
        await gw.close()


@pytest.mark.asyncio
async def test_reconnect_and_close(gateway):
    bus = client(gateway)
    try:
        await bus.read_registers(10105, 1)
        gateway.drop = True
        with pytest.raises(SelfaConnectionError):
            await bus.read_registers(10105, 1)
        assert bus._client is None
        gateway.drop = False
        assert await bus.read_registers(10105, 1) == [2]
    finally:
        await bus.disconnect()
    assert bus._client is None


@pytest.mark.asyncio
async def test_read_write_serialization_and_confirmation(gateway):
    bus = client(gateway)
    try:
        await asyncio.gather(
            bus.read_registers(10105, 1),
            bus.write_and_confirm(50006, 1),
            bus.read_registers(10008, 1),
        )
        assert gateway.words[50006] == 1
        i = next(i for i, r in enumerate(gateway.requests) if r[0] == 6)
        assert gateway.requests[i + 1][:3] == (3, 50006, 1)
        gateway.reject_writes = True
        with pytest.raises(SelfaRegisterError):
            await bus.write_and_confirm(50006, 0)
        assert gateway.words[50006] == 1
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_optional_illegal_registers_do_not_break_polling(hass, gateway):
    regs = tuple(r for r in load_registers() if r.address in {10105, 11032, 11033, 50006})
    gateway.words[11032] = 205
    bus = client(gateway)
    entry = make_entry(gateway)
    coord = SelfahybridCoordinator(hass, entry, bus, regs)
    try:
        data = await coord._async_update_data()
        assert data["temp1"] == 20.5
        assert data["temp2"] is None
        assert coord.unsupported == {"temp2"}
        assert data["unbalanced_output"] == 0
        n = len(gateway.requests)
        await coord._async_update_data()
        assert all(r[1] != 11033 for r in gateway.requests[n:])
        assert all(r[1] != 50006 for r in gateway.requests[n:])
        assert all(r[0] == 3 for r in gateway.requests)
        gateway.drop = True
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()
        assert coord.unsupported == {"temp2"}
    finally:
        await bus.disconnect()


@pytest.mark.asyncio
async def test_all_documented_reads_and_sensor_entities(hass, gateway):
    regs = load_registers()
    for reg in regs:
        for address in range(reg.address, reg.address + reg.count):
            gateway.words.setdefault(address, 0)
    gateway.words[10105] = 2
    gateway.words[33000] = 8750
    gateway.words[30256] = 1
    bus = client(gateway)
    coord = SelfahybridCoordinator(hass, make_entry(gateway), bus, regs)
    try:
        data = await coord._async_update_data()
        assert len(data) == 177
        assert data["soc"] == 87.5
        assert coord.unsupported == set()
        coord.async_set_updated_data(data)
        for reg in regs:
            entity = SelfaRegisterSensor(coord, reg)
            assert entity.available
            assert entity.unique_id.endswith("_" + reg.key)
            assert entity.native_value == data[reg.key]
            assert entity.device_info["manufacturer"] == "Selfa"
        switch = SelfaSwitch(coord, "unbalanced_output")
        await switch.async_turn_on()
        assert switch.is_on is True
        gateway.reject_writes = True
        with pytest.raises(Exception, match="confirm"):
            await switch.async_turn_off()
        assert switch.is_on is True
    finally:
        await bus.disconnect()


def test_configuration_defaults():
    data = connection_schema()({"host": "192.0.2.1"})
    assert data["slave_id"] == 247
    assert data["protocol"] == "rtu_over_tcp"
    assert data["port"] == 502


@pytest.mark.asyncio
async def test_ui_flow_validates_real_gateway_and_serial(hass, gateway):
    from custom_components.selfa_sfh.config_flow import SelfahybridConfigFlow

    flow = SelfahybridConfigFlow()
    flow.hass = hass
    flow.handler = "selfa_sfh"
    flow.context = {"source": "user"}
    flow.flow_id = "test_flow"
    result = await flow.async_step_user(
        {"host": "127.0.0.1", "port": gateway.port, "slave_id": 247, "protocol": "tcp"}
    )
    assert result["type"] == "create_entry"
    assert result["data"]["serial_number"] == "SFH1234567890123"
    assert all(request[0] == 3 for request in gateway.requests)


@pytest.mark.asyncio
async def test_setup_and_unload_lifecycle(hass, gateway):
    from custom_components.selfa_sfh import async_setup_entry, async_unload_entry

    entry = make_entry(gateway)
    with (
        patch("custom_components.selfa_sfh.async_register_cards", new_callable=AsyncMock),
        patch(
            "custom_components.selfa_sfh.SelfahybridCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ),
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
        ) as forward,
        patch.object(
            hass.config_entries, "async_unload_platforms", new_callable=AsyncMock, return_value=True
        ),
    ):
        assert await async_setup_entry(hass, entry)
        assert len(forward.call_args.args[1]) == 4
        assert "ems" not in forward.call_args.args[1]
        assert await async_unload_entry(hass, entry)


@pytest.mark.asyncio
async def test_real_home_assistant_platform_setup(hass, gateway, tmp_path):
    """Load the custom integration and all real entity platforms, not stubs."""
    from pathlib import Path

    from homeassistant.helpers import area_registry, device_registry, entity_registry
    from homeassistant.setup import async_setup_component

    (tmp_path / "custom_components").symlink_to(
        Path.cwd() / "custom_components", target_is_directory=True
    )
    hass.config.skip_pip = True
    await area_registry.async_load(hass)
    await device_registry.async_load(hass)
    await entity_registry.async_load(hass)
    for register in load_registers():
        for address in range(register.address, register.address + register.count):
            gateway.words.setdefault(address, 0)
    gateway.words[10105] = 2
    gateway.words[33000] = 8750
    assert await async_setup_component(hass, "selfa_sfh", {})
    entry = make_entry(gateway, options={"request_delay": 0})
    await hass.config_entries.async_add(entry)
    await hass.async_block_till_done()
    assert entry.state.value == "loaded"
    states = [state for state in hass.states.async_all() if "selfa_key" in state.attributes]
    assert len(states) == 183
    assert next(state for state in states if state.attributes["selfa_key"] == "soc").state == "87.5"
    assert all(req[0] == 3 for req in gateway.requests)
    coordinator = entry.runtime_data
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert coordinator.client._client is None
