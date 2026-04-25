"""Modbus client wrapper for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import (
    AsyncModbusTcpClient,
    AsyncModbusUdpClient,
    AsyncModbusSerialClient,
)
from pymodbus.exceptions import ModbusException

from .const import DEFAULT_SLAVE_ID

_LOGGER = logging.getLogger(__name__)


class SelfahybridModbusClient:
    """Async Modbus client with auto-reconnect for Selfa SFH."""

    def __init__(
        self,
        host: str,
        port: int,
        slave_id: int = DEFAULT_SLAVE_ID,
        protocol: str = "tcp",
    ) -> None:
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._protocol = protocol
        self._client: AsyncModbusTcpClient | AsyncModbusUdpClient | None = None

    def _create_client(self) -> None:
        if self._protocol == "udp":
            self._client = AsyncModbusUdpClient(host=self._host, port=self._port)
        else:
            # Both "tcp" and "rtu_over_tcp" use AsyncModbusTcpClient;
            # RTU framing is handled at register level by specifying the slave ID.
            self._client = AsyncModbusTcpClient(host=self._host, port=self._port)

    async def connect(self) -> bool:
        """Establish connection, return True on success."""
        if self._client is None:
            self._create_client()
        try:
            connected = await self._client.connect()
            return connected
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Failed to connect to %s:%s — %s", self._host, self._port, exc)
            return False

    async def disconnect(self) -> None:
        """Close the Modbus connection."""
        if self._client and self._client.connected:
            self._client.close()

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.connected

    async def _ensure_connected(self) -> bool:
        if not self.connected:
            return await self.connect()
        return True

    async def read_registers(self, address: int, count: int) -> list[int] | None:
        """Read *count* holding registers starting at *address*.

        Returns a list of raw register values or None on error.
        """
        if not await self._ensure_connected():
            return None
        try:
            result = await self._client.read_holding_registers(
                address=address, count=count, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.debug("Modbus error reading @%04X: %s", address, result)
                return None
            return result.registers
        except ModbusException as exc:
            _LOGGER.warning("ModbusException @%04X: %s", address, exc)
            return None
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Unexpected error reading @%04X: %s", address, exc)
            self._client = None  # Force reconnect next time
            return None

    async def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register. Returns True on success."""
        if not await self._ensure_connected():
            return False
        try:
            result = await self._client.write_register(
                address=address, value=value, slave=self._slave_id
            )
            if result.isError():
                _LOGGER.warning("Modbus write error @%04X: %s", address, result)
                return False
            return True
        except ModbusException as exc:
            _LOGGER.warning("ModbusException writing @%04X: %s", address, exc)
            return False
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Unexpected error writing @%04X: %s", address, exc)
            self._client = None
            return False

    async def read_u16(self, address: int) -> int | None:
        """Read a single unsigned 16-bit register."""
        regs = await self.read_registers(address, 1)
        return regs[0] if regs is not None else None

    async def read_i16(self, address: int) -> int | None:
        """Read a signed 16-bit register."""
        regs = await self.read_registers(address, 1)
        if regs is None:
            return None
        val = regs[0]
        return val if val < 0x8000 else val - 0x10000

    async def read_u32(self, address: int) -> int | None:
        """Read two consecutive registers as an unsigned 32-bit value (big-endian)."""
        regs = await self.read_registers(address, 2)
        if regs is None:
            return None
        return (regs[0] << 16) | regs[1]

    async def read_i32(self, address: int) -> int | None:
        """Read two consecutive registers as a signed 32-bit value."""
        regs = await self.read_registers(address, 2)
        if regs is None:
            return None
        val = (regs[0] << 16) | regs[1]
        return val if val < 0x80000000 else val - 0x100000000
