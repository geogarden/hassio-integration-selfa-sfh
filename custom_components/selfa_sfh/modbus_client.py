"""Serialized, paced Modbus exchanges over an Ethernet-to-RS485 gateway."""

from __future__ import annotations

import asyncio
import time

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusUdpClient
from pymodbus.exceptions import ModbusException
from pymodbus.framer import FramerType


class SelfaConnectionError(Exception):
    """Transport failure; retry without blacklisting register addresses."""


class SelfaRegisterError(Exception):
    """The inverter responded with a Modbus exception."""

    def __init__(self, address: int, code: int) -> None:
        super().__init__(f"Register {address}: Modbus exception {code}")
        self.address, self.code = address, code


class SelfahybridModbusClient:
    """One socket, one exchange in flight, real RTU framing where selected."""

    def __init__(
        self,
        host: str,
        port: int,
        slave_id: int = 247,
        protocol: str = "rtu_over_tcp",
        *,
        timeout: float = 3,
        request_delay: float = 0.2,
    ) -> None:
        self.host, self.port, self.slave_id = host, port, slave_id
        self.protocol, self.timeout = protocol, timeout
        self.request_delay = request_delay
        self._client = None
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    def _create_client(self):
        kwargs = {"host": self.host, "port": self.port, "timeout": self.timeout, "retries": 0}
        if self.protocol == "udp":
            return AsyncModbusUdpClient(**kwargs, framer=FramerType.SOCKET)
        framer = FramerType.RTU if self.protocol == "rtu_over_tcp" else FramerType.SOCKET
        return AsyncModbusTcpClient(**kwargs, framer=framer)

    def _close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def _connect(self) -> None:
        if self._client is not None and self._client.connected:
            return
        self._close()
        self._client = self._create_client()
        try:
            async with asyncio.timeout(self.timeout + 1):
                if not await self._client.connect():
                    raise SelfaConnectionError("Gateway did not accept the connection")
        except asyncio.CancelledError:
            self._close()
            raise
        except (TimeoutError, OSError, ModbusException, SelfaConnectionError) as err:
            self._close()
            raise SelfaConnectionError(str(err)) from err

    async def connect(self) -> None:
        """Open a socket; only a read verifies the protocol and unit ID."""
        async with self._lock:
            await self._connect()

    async def disconnect(self) -> None:
        """Always release the socket, including disconnected clients."""
        async with self._lock:
            self._close()

    async def _exchange(self, method: str, **kwargs):
        await self._connect()
        delay = self.request_delay - (time.monotonic() - self._last_request)
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            async with asyncio.timeout(self.timeout + 1):
                response = await getattr(self._client, method)(device_id=self.slave_id, **kwargs)
        except asyncio.CancelledError:
            self._close()
            raise
        except (TimeoutError, OSError, ModbusException) as err:
            self._close()
            raise SelfaConnectionError(str(err)) from err
        finally:
            self._last_request = time.monotonic()
        if response is None:
            self._close()
            raise SelfaConnectionError("Empty Modbus response")
        if response.isError():
            code = getattr(response, "exception_code", None)
            if code is None:
                raise SelfaConnectionError(str(response))
            raise SelfaRegisterError(kwargs["address"], code)
        return response

    async def read_registers(self, address: int, count: int) -> list[int]:
        """Read function 03 with the document's addresses, no -1 offset."""
        async with self._lock:
            response = await self._exchange("read_holding_registers", address=address, count=count)
            if len(response.registers) != count:
                raise SelfaConnectionError(f"Short response at {address}")
            return list(response.registers)

    async def write_and_confirm(self, address: int, value: int) -> int:
        """Write and confirm under one lock; caller enforces the allowlist."""
        async with self._lock:
            await self._exchange("write_register", address=address, value=value)
            response = await self._exchange("read_holding_registers", address=address, count=1)
            if len(response.registers) != 1 or response.registers[0] != value:
                raise SelfaConnectionError("Inverter did not confirm the requested switch state")
            return response.registers[0]
