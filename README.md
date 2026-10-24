# Selfa SFH — Home Assistant przez bramkę RS485

<img src="custom_components/selfa_sfh/brand/icon.png" alt="Selfa SFH" width="96">

Wersja **2.1.0**. Bezpośrednie połączenie z falownikiem Selfa SFH przez
bramkę Ethernet/Wi-Fi ↔ RS485. ESPHome nie jest potrzebne.

```mermaid
flowchart LR
  HA[Home Assistant] <-->|TCP lub RTU przez TCP| GW[Bramka RS485]
  GW <-->|Modbus RTU| SFH[Selfa SFH]
```

## Co zawiera

- 100 pozycji tabeli odczytowej z dostarczonego `SFH-modbus.pdf`, w tym dane PV,
  wszystkie fazy sieci i backup, moce, energie, temperatury, baterię i pełne dane BMS.
- 75 dodatkowych rejestrów ustawień do podglądu oraz stany dwóch przełączników:
  razem **177 adresów logicznych**. Rejestry 32-bitowe zajmują po dwa słowa.
- 179 sensorów (177 wartości rejestrów + opis trybu pracy i kierunku baterii),
  dwa przełączniki, diagnostyka połączenia i przycisk ponowienia brakujących odczytów.
- Prawdziwe ramki **RTU przez TCP** dla transparentnych serwerów szeregowych,
  standardowy **Modbus TCP** dla bramek konwertujących protokół oraz kompatybilność UDP.
- Konfiguracja przez interfejs HA, zmiana IP/portu bez usuwania integracji,
  osobne częstotliwości odczytu danych i ustawień.
- Karta `custom:selfa-card`, ładowana automatycznie jak w integracji Wanas:
  schemat PV u góry / sieć po lewej / bateria po prawej / falownik pośrodku / dom na dole,
  animowane przepływy, osobny odczyt backup, dane PV1/PV2, baterii, dzienne i fazowe.
  Arial, duże wartości, obsługa polskiego i angielskiego.
- Grupowanie tylko udokumentowanych, sąsiadujących rejestrów, blokada wspólnych
  operacji RS485, przerwy między zapytaniami i ponowne połączenie po awarii.
- Nieobsługiwany opcjonalny rejestr nie blokuje pozostałych odczytów. Jest
  pomijany do ponowienia przyciskiem „Ponów brakujące odczyty” lub przeładowania integracji.

## Instalacja przez HACS

1. HACS → menu → **Niestandardowe repozytoria**.
2. Dodaj `https://github.com/geogarden/hassio-integration-selfa-sfh`, kategoria **Integracja**.
3. Pobierz **Selfa SFH** i uruchom ponownie Home Assistant.
4. Ustawienia → Urządzenia i usługi → Dodaj integrację → **Selfa SFH**.

Instalacja ręczna: skopiuj cały katalog `custom_components/selfa_sfh` do
`/config/custom_components/selfa_sfh` i zrestartuj HA. Wymagany HA 2025.1 lub nowszy.

## Podłączenie bramki

1. Podłącz A/B bramki do właściwego portu komunikacyjnego RS485 falownika,
   zgodnie z oznaczeniami i instrukcją obu urządzeń. Nie używaj portu BMS/CAN baterii.
2. Ustaw port szeregowy bramki tak jak działające ESPHome: **9600 bit/s, 8N1**
   (8 bitów danych, brak parzystości, 1 bit stopu), jeżeli nie zmieniono tego w falowniku.
3. Wybierz tryb **TCP Server** bramki i sprawdź jej rzeczywisty port nasłuchu.
   Port nie musi wynosić 502; niektóre serwery używają np. 8899 lub innej ustawionej wartości.
4. Podaj w integracji **IP bramki**, a nie dawny adres ESPHome `192.168.88.44`.
5. Przed uruchomieniem tej integracji zatrzymaj odczyty ESPHome z tej samej
   magistrali. Dwa niezależne mastery na jednej RS485 mogą zakłócać odpowiedzi.

| Pole | Ustawienie |
|---|---|
| Host | Rzeczywisty IP / nazwa sieciowa bramki RS485 |
| Port | Port TCP Server skonfigurowany w bramce; domyślnie 502 |
| Unit ID | **247**, zgodnie z dotychczasowym ESPHome |
| `rtu_over_tcp` | Transparentny serwer szeregowy: przenosi surowe ramki RTU z CRC |
| `tcp` | Bramka konwertująca Modbus TCP (nagłówek MBAP) na Modbus RTU |
| `udp` | Modbus UDP z nagłówkiem MBAP; nie jest to transparentne RTU przez UDP |

Przy dodawaniu integracja sprawdza odczyt rejestrów **10008** i **10105**.
Samo otwarcie portu TCP nie jest uznawane za prawidłowe połączenie z falownikiem.
O ile falownik udostępnia numer seryjny, jest on używany do wykrywania duplikatów.

Opcje integracji: dane bieżące domyślnie **30 s**, ustawienia **300 s**, przerwa
między zapytaniami **200 ms**, limit odpowiedzi **3 s**. Dla wolnej bramki można
zwiększyć odstępy i timeout. Dane po utracie połączenia stają się niedostępne.

## Karta na pulpicie

Edytuj pulpit, dodaj kartę **Selfa SFH** albo wklej:

```yaml
type: custom:selfa-card
title: Selfa SFH 8.1
```

Dla kilku falowników opcjonalnie dodaj `device_id` urządzenia z rejestru HA.
Karta rozpoznaje encje po kluczach integracji, więc zmiana ich nazw w HA nie
wymaga poprawiania konfiguracji karty. Nie wymaga zewnętrznych kart ani bibliotek.

Plik karty jest udostępniany automatycznie pod
`/selfa_sfh_static/selfa-card.js?v=2.1.0` po załadowaniu integracji.
Po aktualizacji uruchom ponownie HA i odśwież stronę przez Ctrl+F5.
Animacje można wyłączyć przez `animate: false`; karta respektuje też preferencję
ograniczenia ruchu przeglądarki. Przy braku połączenia przepływy są zatrzymane.
Panele szczegółów PV1/PV2, sześć energii dziennych i tabela faz są stale widoczne;
sterowanie rozwija się poniżej schematu.

## Znaczenie odczytów i sterowania

- Adresy z dokumentacji są używane bez odejmowania 1. Nie stosujemy starej,
  niezgodnej mapy `0x0000…0x00AD` z wersji 1.0.0 tego repozytorium.
- U16/I16/U32/I32, kolejność big-endian i dzielniki pochodzą z tabeli PDF.
  `SOC` i `SOH` mają dzielnik 100; moce w kW zwykle 1000.
- Kierunek baterii pochodzi z **30256**: 0 = rozładowywanie, 1 = ładowanie.
  Ten rejestr nie określa osobnego stanu oczekiwania. Nie zgadujemy kierunku
  na podstawie znaku prądu lub mocy. Karta wyświetla „Oczekiwanie”, gdy bezwzględna
  moc baterii jest mniejsza od 0,01 kW; jest to próg wizualny, nie dodatkowy stan BMS.
- Wykres pokazuje moce sieci i baterii ze znakiem zwracanym przez falownik.
  Moc domu jest szacunkiem bilansu AC: `P_AC − eksport netto z licznika`.
  Domyślnie dodatnia moc licznika oznacza eksport; dla odwrotnej konwencji dodaj
  `grid_export_positive: false` do konfiguracji karty. Szacunek wymaga licznika
  obejmującego całą instalację; nie zastępuje dedykowanego pomiaru zużycia domu.
  Backup jest pokazany osobno i nie jest ponownie dodawany do bilansu.
- Energia PV w panelu dziennym pochodzi z **31005**. Rejestry **11018/11020**
  są nazwane energią inwertera, bo PDF opisuje je jako `Energy-today/total`.
- Limity opisane w PDF jako `N/A` z dzielnikiem 1000 pozostają ułamkami według
  tabeli, bez dopisywania niepotwierdzonej jednostki %. Ich atrybuty pokazują adres i dzielnik.
- Czasy zabezpieczeń w jednostce `Prd` pozostają w jednostce producenta,
  a zapakowane godziny harmonogramów mają atrybut `time` z formatem HH:MM.
- Temperatury BMS mają typ U16 zgodnie z tabelą; nie stosujemy nieudokumentowanego
  przesunięcia ani zmiany na typ ze znakiem.
- Dwa przełączniki zapisują wyłącznie **50006** (asymetria On-Grid) i **50007**
  (Peak Load Shifting), wartości 0/1. Po zapisie następuje odczyt potwierdzający.
  Nie ma zapisu przy dodawaniu integracji ani przy zwykłym odświeżaniu danych.
- Rejestry WO, emulacja BMS i pola zarezerwowane są pominięte. Harmonogramy,
  zabezpieczenia i pozostałe ustawienia są dostępne wyłącznie do podglądu.

## Aktualizacja z wersji 1.0.0

Zachowano domenę `selfa_sfh`, wpis połączenia i klucze istniejących pomiarów,
aby ich identyfikatory encji mogły pozostać stabilne. Parametry starego połączenia
(także stary Unit ID 1) nie są zmieniane automatycznie — popraw je przez
**Zmień konfigurację**, jeżeli dotyczą innego ustawienia niż działające ESPHome.

Stare encje `select`, `number`, przełączniki limitu eksportu / trybu off-grid oraz
usługi EMS nie są już tworzone: poprzednia implementacja używała niewłaściwej
mapy adresów. Zastępują je poprawne odczyty ustawień i dwa przełączniki z ESPHome.
Nie usuwamy ręcznie wpisów użytkownika z rejestru encji HA; stare nieużywane encje
można usunąć w ustawieniach po sprawdzeniu nowej integracji.

**Statystyki historyczne starej wersji mogą mieć błędną skalę** (zwłaszcza moc i SOC).
Nowe odczyty mają skalę z PDF; aktualizacja nie przelicza starych danych w bazie HA.

Pełna tabela protokołu nie gwarantuje, że firmware konkretnego falownika obsłuży
każdy rejestr. Instalację na fizycznym SFH trzeba zweryfikować po podłączeniu bramki.

## Testy deweloperskie

```bash
pip install 'homeassistant==2025.1.4' 'pymodbus>=3.10.0,<4.0.0' pytest pytest-asyncio ruff
python -m pytest tests -q
ruff check custom_components tests
node --check custom_components/selfa_sfh/www/selfa-card.js
```

Testy uruchamiają lokalny serwer symulujący ramki Modbus TCP oraz RTU przez TCP
z CRC. Sprawdzają dekodowanie, skalowanie, Unit ID 247, potwierdzanie zapisów,
rozłączenie / ponowne połączenie i pomijanie nieobsługiwanych rejestrów.
Nie łączą się z urządzeniami użytkownika.

## Ikona integracji

Ikona Selfa znajduje się w `custom_components/selfa_sfh/brand/` jako `icon.png` (256×256) i `icon@2x.png` (512×512), z przezroczystym tłem. Home Assistant 2026.3 lub nowszy wyświetla ją automatycznie po aktualizacji integracji i restarcie; w razie potrzeby odśwież interfejs przez Ctrl+F5. Starsze wersje HA nie obsługują lokalnych ikon `brand/`.

Źródło grafiki: [Selfa PV](https://www.selfa-pv.com/materials/icon_oferta_svg_2/icon10.svg). Zachowano oryginalny kształt i kolor.

