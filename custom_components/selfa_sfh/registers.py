"""Documented register map and protocol logic, independent of Home Assistant."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Register:
    """One value spanning one or more 16-bit registers."""

    key: str
    name: str
    address: int
    count: int
    data_type: str
    divisor: int = 1
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    slow: bool = False
    diagnostic: bool = False


def load_registers() -> tuple[Register, ...]:
    """Load in HA's executor, not in its event loop."""
    path = Path(__file__).with_name("registers.json")
    return tuple(Register(**item) for item in json.loads(path.read_text()))


def decode_value(register: Register, words: dict[int, int]) -> int | float | str | None:
    """Decode big-endian values without ESPHome's float32 rounding."""
    values = [words.get(register.address + i) for i in range(register.count)]
    if any(word is None for word in values):
        return None
    if register.data_type == "STR":
        raw = b"".join(word.to_bytes(2, "big") for word in values)
        return raw.rstrip(b"\x00\xff ").decode("ascii", errors="replace").strip()
    raw = 0
    for word in values:
        raw = (raw << 16) | word
    bits = 16 * register.count
    if register.data_type.startswith("I") and raw & (1 << (bits - 1)):
        raw -= 1 << bits
    return raw if register.divisor == 1 else raw / register.divisor


def read_blocks(registers: list[Register], max_words: int = 32) -> list[list[Register]]:
    """Batch adjacent documented words; no gaps or split multiword values."""
    result: list[list[Register]] = []
    for register in sorted(registers, key=lambda item: item.address):
        if result:
            start = result[-1][0].address
            end = result[-1][-1].address + result[-1][-1].count
            if register.address == end and register.address + register.count - start <= max_words:
                result[-1].append(register)
                continue
        result.append([register])
    return result
