"""Named bits from PDF table 3.3; unknown bits are never discarded."""

FAULTS = {
    "fault_flag1": dict(enumerate([
        "Brak sieci", "Nieprawidłowe napięcie sieci", "Nieprawidłowa częstotliwość sieci",
        "Błąd DCI", "Przekroczony limit izolacji", "Błąd GFCI", "Za wysokie napięcie PV",
        "Błąd napięcia magistrali DC", "Przegrzanie falownika",
    ])),
    "fault_flag2": {1: "Błąd SPI", 2: "Błąd E2", 3: "Błąd przetwornika GFCI",
        4: "Błąd przetwornika AC", 5: "Błąd przekaźnika", 6: "Błąd wentylatora wewnętrznego",
        7: "Błąd wentylatora zewnętrznego"},
    "fault_flag3": dict(enumerate([
        "Błąd sprzętowy magistrali DC", "Za mała moc PV", "Błąd napięcia baterii",
        "Błąd napięcia backup", "Za niskie napięcie magistrali DC", "Błąd sprzętowy systemu",
        "Przeciążenie backup", "Za wysokie napięcie falownika",
        "Za wysoka częstotliwość falownika", "Za duży prąd falownika", "Kolejność faz",
    ])),
    "arm_fault_flag": {0: "Błąd SCI", 1: "Błąd FLASH", 2: "Błąd komunikacji z licznikiem"},
}


def fault_attributes(key, value):
    if not isinstance(value, int):
        return {}
    names = FAULTS.get(key, {})
    bits = [bit for bit in range(32) if value & (1 << bit)]
    return {"active_bits": bits,
            "active_faults": [names.get(bit, f"Nieopisany bit {bit}") for bit in bits],
            "unknown_bits": [bit for bit in bits if bit not in names]}
