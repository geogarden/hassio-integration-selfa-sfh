"""A local wire-level Modbus gateway; never connects to a user's inverter."""

from __future__ import annotations

import asyncio
import struct
from types import MappingProxyType

import pytest_asyncio
from homeassistant import loader
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from pymodbus.framer.rtu import FramerRTU


class Gateway:
    def __init__(self, protocol="tcp"):
        self.protocol = protocol
        self.words = {10008: 0x1E03, 10105: 2, 50006: 0, 50007: 0}
        serial = b"SFH1234567890123"
        self.words.update(
            {10000 + i // 2: int.from_bytes(serial[i : i + 2], "big") for i in range(0, 16, 2)}
        )
        self.requests = []
        self.writers = set()
        self.server = None
        self.drop = False
        self.reject_writes = False

    async def start(self):
        self.server = await asyncio.start_server(self.handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def close(self):
        self.server.close()
        await self.server.wait_closed()
        for writer in list(self.writers):
            writer.close()
            await writer.wait_closed()

    async def handle(self, reader, writer):
        self.writers.add(writer)
        try:
            while True:
                if self.protocol == "tcp":
                    header = await reader.readexactly(7)
                    transaction, proto, length, unit = struct.unpack(">HHHB", header)
                    assert proto == 0
                    pdu = await reader.readexactly(length - 1)
                else:
                    request = await reader.readexactly(8)
                    assert FramerRTU.compute_CRC(request[:-2]) == int.from_bytes(
                        request[-2:], "big"
                    )
                    unit, pdu = request[0], request[1:6]
                function, address, value = struct.unpack(">BHH", pdu)
                self.requests.append((function, address, value, unit))
                if self.drop:
                    writer.close()
                    return
                if unit != 247:
                    continue
                if function == 3:
                    words = [self.words.get(a) for a in range(address, address + value)]
                    response = (
                        bytes([0x83, 2])
                        if any(v is None for v in words)
                        else bytes([3, value * 2]) + b"".join(v.to_bytes(2, "big") for v in words)
                    )
                elif function == 6:
                    if self.reject_writes:
                        response = bytes([0x86, 3])
                    else:
                        self.words[address] = value
                        response = pdu
                else:
                    response = bytes([function | 0x80, 1])
                if self.protocol == "tcp":
                    frame = struct.pack(">HHHB", transaction, 0, len(response) + 1, unit) + response
                else:
                    frame = bytes([unit]) + response
                    frame += FramerRTU.compute_CRC(frame).to_bytes(2, "big")
                writer.write(frame)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            self.writers.discard(writer)
            writer.close()


def make_entry(gateway, *, options=None):
    return ConfigEntry(
        version=2,
        minor_version=1,
        domain="selfa_sfh",
        title="Selfa test",
        data={
            "host": "127.0.0.1",
            "port": gateway.port,
            "slave_id": 247,
            "protocol": gateway.protocol,
        },
        options=options or {},
        source="user",
        unique_id="SFH1234567890123",
        discovery_keys=MappingProxyType({}),
    )


@pytest_asyncio.fixture
async def gateway():
    gw = await Gateway().start()
    yield gw
    await gw.close()


@pytest_asyncio.fixture
async def hass(tmp_path):
    h = HomeAssistant(str(tmp_path))
    loader.async_setup(h)
    h.config_entries = ConfigEntries(h, {})
    yield h
    await h.async_stop(force=True)
