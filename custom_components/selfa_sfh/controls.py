"""Explicit SFH writable register definitions; never accept arbitrary addresses."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Control:
    key: str
    address: int
    name: str
    kind: str
    choices: tuple[tuple[str, int], ...] = ()
    scale: int = 1
    minimum: float = 0
    maximum: float = 65535
    step: float = 1
    unit: str | None = None
    signed: bool = False
    advanced: bool = False
    power: bool = False
    bit: int | None = None

    def encode(self, value) -> int:
        if self.kind == "select":
            try:
                return dict(self.choices)[value]
            except (KeyError, TypeError) as err:
                raise ValueError("Unsupported selection") from err
        if self.kind == "switch":
            if not isinstance(value, bool):
                raise ValueError("A boolean is required")
            return int(value)
        if self.kind == "time":
            if value.second or value.microsecond or value.tzinfo is not None:
                raise ValueError("Use local hours and minutes only")
            return value.hour * 256 + value.minute
        try:
            number = Decimal(str(value))
            if not number.is_finite() or not Decimal(str(self.minimum)) <= number <= Decimal(str(self.maximum)):
                raise ValueError("Value outside documented bounds")
            ticks = (number - Decimal(str(self.minimum))) / Decimal(str(self.step))
            if ticks != ticks.to_integral_value():
                raise ValueError("Value does not match the documented step")
            if self.address == 25120 and abs(number) < Decimal("0.8"):
                raise ValueError("Power factor must be in [-1,-0.8] or [0.8,1]")
            raw = number * self.scale
            if raw != raw.to_integral_value():
                raise ValueError("Value cannot be encoded exactly")
            raw = int(raw)
        except (InvalidOperation, TypeError) as err:
            raise ValueError("Invalid numeric value") from err
        low, high = (-32768, 32767) if self.signed else (0, 65535)
        if not low <= raw <= high:
            raise ValueError("Value does not fit a register")
        return raw & 65535

    def decode(self, raw: int):
        if self.kind == "select":
            return next((label for label, code in self.choices if code == raw), None)
        if self.kind == "switch":
            return bool(raw & (1 << self.bit)) if self.bit is not None else bool(raw)
        if self.signed and raw & 32768:
            raw -= 65536
        return raw / self.scale


def select(key, address, name, choices, advanced=False):
    return Control(key, address, name, "select", tuple(choices.items()), advanced=advanced)


CONTROLS = [
    select("operating_mode", 50000, "Tryb pracy", {
        "general": 0x0101, "economic": 0x0102, "ups": 0x0103,
        "off_grid": 0x0200, "ems_ac": 0x0301, "ems_general": 0x0302,
        "ems_battery": 0x0303, "ems_off_grid": 0x0304,
    }),
    Control("ups_enabled", 50001, "Funkcja UPS", "switch"),
    Control("unbalanced_output", 50006, "Asymetria On-Grid", "switch"),
    Control("peak_load_shifting", 50007, "Peak Load Shifting", "switch"),
    Control("export_limit_enabled", 25100, "Ograniczenie oddawania do sieci", "switch"),
    Control("export_limit_percent", 25103, "Limit oddawania do sieci", "number", scale=10, maximum=100, step=0.1, unit="%"),
    select("ac_control_mode", 50202, "Sterowanie mocą AC", {"off": 0, "total": 1, "per_phase": 2}, True),
    select("power_priority", 50210, "Priorytet oddawania mocy", {"pv": 0, "battery": 1}, True),
    Control("on_grid_soc_protection", 52502, "Ochrona SOC on-grid", "switch"),
    Control("off_grid_soc_protection", 52504, "Ochrona SOC off-grid", "switch"),
    Control("on_grid_end_soc", 52503, "Minimalny SOC on-grid", "number", scale=10, maximum=100, step=0.1, unit="%"),
    Control("off_grid_end_soc", 52505, "Minimalny SOC off-grid", "number", scale=10, maximum=100, step=0.1, unit="%"),
    select("parallel_role", 50010, "Praca równoległa", {"independent": 0, "slave": 1, "master": 2}, True),
    select("overload_method", 25015, "Sposób obsługi przeciążenia", {"rated": 0, "overload_110": 1, "limit": 2}, True),
    select("reactive_mode", 25121, "Regulacja mocy biernej", {"off": 0, "pf": 1, "qt": 2, "qp": 3, "qu": 4}, True),
    Control("reactive_limit", 25118, "Limit mocy biernej", "number", scale=10, minimum=-60, maximum=60, step=0.1, unit="%", signed=True, advanced=True),
    Control("power_factor", 25120, "Współczynnik mocy PF", "number", scale=1000, minimum=-1, maximum=1, step=0.001, signed=True, advanced=True),
    select("battery_brand", 52500, "Konfiguracja baterii", {"brand_1": 1, "external_ems": 2, "wattsonic": 10, "aoboet": 11, "dyness": 12, "pylon": 13, "soluna": 14, "sheenplus": 15, "weco": 16}, True),
]

# Power bounds here are encoding bounds. A commissioned installation limit is
# additionally mandatory before these controls can be used.
for key, address, name, signed in [
    ("ac_target", 50203, "Zadana moc AC", True),
    ("phase_a_target", 50204, "Zadana moc fazy A", True),
    ("phase_b_target", 50205, "Zadana moc fazy B", True),
    ("phase_c_target", 50206, "Zadana moc fazy C", True),
    ("battery_target", 50207, "Zadana moc baterii", True),
    ("ac_upper_limit", 50208, "Górny limit mocy AC", True),
    ("ac_lower_limit", 50209, "Dolny limit mocy AC", True),
    ("pv_target", 50211, "Zadana moc PV", False),
]:
    CONTROLS.append(Control(key, address, name, "number", scale=100,
        minimum=-327.68 if signed else 0, maximum=327.67 if signed else 655.35,
        step=0.01, unit="kW", signed=signed, advanced=True, power=True))
CONTROLS.append(Control("max_grid_power", 50009, "Maksymalna moc sieci", "number",
    scale=10, maximum=6553.5, step=0.1, unit="kVA", power=True))

for index in range(6):
    slot, base = index + 1, 53007 + index * 7
    CONTROLS.extend([
        Control(f"period_{slot}_enabled", 53006, f"Okres {slot} — aktywny", "switch", bit=index),
        select(f"period_{slot}_action", base, f"Okres {slot} — działanie", {"none": 0, "charge": 1, "discharge": 2}),
        select(f"period_{slot}_source", base+1, f"Okres {slot} — źródło ładowania", {"pv": 0, "pv_grid": 1}),
        Control(f"period_{slot}_power", base+3, f"Okres {slot} — limit mocy", "number", scale=10, maximum=100, step=0.1, unit="%"),
        Control(f"period_{slot}_start", base+5, f"Okres {slot} — początek", "time"),
        Control(f"period_{slot}_end", base+6, f"Okres {slot} — koniec", "time"),
    ])

for address, key, name, low, high, scale, unit in [
    (28000, "recovery_voltage_low", "Dolny próg napięcia powrotu", 55, 230, 10, "V"),
    (28001, "recovery_voltage_high", "Górny próg napięcia powrotu", 230, 300, 10, "V"),
    (28002, "recovery_frequency_low", "Dolny próg częstotliwości powrotu", 45, 65, 100, "Hz"),
    (28003, "recovery_frequency_high", "Górny próg częstotliwości powrotu", 45, 65, 100, "Hz"),
    (28004, "undervoltage_threshold", "Próg ochrony podnapięciowej", 55, 230, 10, "V"),
    (28006, "overvoltage_threshold", "Próg ochrony nadnapięciowej", 230, 300, 10, "V"),
    (28012, "underfrequency_threshold", "Próg ochrony podczęstotliwościowej", 45, 65, 100, "Hz"),
    (28014, "overfrequency_threshold", "Próg ochrony nadczęstotliwościowej", 45, 65, 100, "Hz"),
    (50005, "off_grid_frequency", "Częstotliwość off-grid", 45, 65, 100, "Hz"),
]:
    CONTROLS.append(Control(key, address, name, "number", scale=scale,
        minimum=low, maximum=high, step=1/scale, unit=unit, advanced=True))
for address in (28005, 28007, 28013, 28015):
    CONTROLS.append(Control(f"protection_duration_{address}", address,
        f"Czas zabezpieczenia {address} (Prd)", "number", minimum=1,
        maximum=50000, advanced=True))

CONTROLS.append(select("battery_protocol_control", 52501, "Protokół baterii (marka 1)", {"protocol_0": 0, "protocol_1": 1, "ebs_5150": 2}, True))
BY_KEY = {control.key: control for control in CONTROLS}


def valid_time(raw: int) -> bool:
    return 0 <= raw >> 8 <= 23 and 0 <= raw & 255 <= 59


def validate_period(start: int, end: int) -> None:
    if not valid_time(start) or not valid_time(end) or start == end:
        raise ValueError("Period needs valid, different start and end times")
