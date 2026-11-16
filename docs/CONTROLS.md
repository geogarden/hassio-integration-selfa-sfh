# Selfa SFH — sterowanie i harmonogram

Wersja 2.3.0. Funkcje zapisu sprawdzono na symulatorze, bez zapisów do fizycznego falownika.

## Zakres

77 definicji sterowania: 20 list wyboru, 33 pola liczbowe, 12 przełączników
(w tym 2 istniejące) i 12 godzin harmonogramu. Dodatkowo synchronizacja
zegara oraz 3 polecenia serwisowe tylko do zapisu.

- Tryb pracy 50000: ogólny, ekonomiczny, UPS, off-grid i 4 tryby EMS.
- Włączenie UPS, limit oddawania do sieci i próg procentowy.
- Ochrona SOC oraz minimalny SOC on-grid/off-grid w procentach.
- 6 okresów: aktywność, działanie, źródło ładowania, limit mocy, początek i koniec.
- Zadawanie mocy łącznej AC, poszczególnych faz, baterii i PV; limity AC oraz priorytet PV/baterii.
- Ustawienia serwisowe: praca równoległa, konfiguracja baterii,
  wybrane ustawienia protokołu dla marki 1, regulacja mocy biernej/PF,
  udokumentowane progi zabezpieczeń i częstotliwość off-grid.
- Opisy bitów błędów falownika z tabeli 3.3; zachowane nieznane bity i kody BMS.

Dotychczasowe 177 surowych odczytów i identyfikatory encji pozostają zachowane.
Nowe encje sterujące mają własne identyfikatory. Istniejące przełączniki
asymetrii i Peak Load Shifting zachowują swoje identyfikatory.
Karta pełna i mini pozostają bez zmian.

## Zasady zapisu

Zwykłe ustawienia: FC06 oraz odczyt kontrolny FC03. Stan encji zmienia się
dopiero po zgodnym potwierdzeniu. Błąd nie jest prezentowany jako sukces.
Odczyty i zapisy są kolejkowane na tej samej magistrali.

Zmiana aktywności okresu czyta aktualną maskę i zachowuje inne okresy oraz
bity zarezerwowane. Włączenie wymaga poprawnych i różnych godzin.
Przed edycją godzin trzeba wyłączyć dany okres. Obsługiwane są okresy
przechodzące przez północ. Kodowanie czasu: godzina w starszym bajcie,
minuta w młodszym — nie liczba dziesiętna HHMM.

Synchronizacja zegara jest ręczna i używa lokalnego czasu HA. Trzy pola
zapisywane są kolejno. W razie błędu komunikat wskazuje możliwość częściowej
zmiany; nie ma obietnicy atomowości ani automatycznego wycofania.

Polecenia WO: włączenie/wyłączenie funkcji off-grid (50200) i skasowanie
flagi przeciążenia off-grid (50201). To przyciski bez fikcyjnego stanu;
potwierdzenie Modbus oznacza przyjęcie polecenia, nie potwierdza jego skutku.

## Opcje integracji

- Limit mocy instalacji dla zapisów: domyślnie 0, czyli zapisy mocy wyłączone.
  Wprowadź potwierdzony limit właściwy dla instalacji. Wspólny pułap jest
  stosowany liczbowo do pól kW i kVA; nie zastępuje pełnego modelu ograniczeń
  falownika, faz, baterii i przyłącza.
- Zapisy serwisowe: domyślnie wyłączone. Zaawansowane encje są dodatkowo
  domyślnie wyłączone w rejestrze HA.
- Wybór trybów EMS: osobne ustawienie eksperckie, domyślnie wyłączone.
  Ta integracja nie implementuje ciągłego zewnętrznego EMS ani emulacji
  licznika/BMS. Sam wybór trybu nie zapewnia takiego sterowania.

## Celowe ograniczenia dokumentacji

- 53500–53523 oraz 25104/25105/25107/25109 to wejścia zapisywane przez
  zewnętrzny EMS. Nie są udawane jako dodatkowe pomiary ani automatycznie zapisywane.
- Nie zapisujemy rejestrów zarezerwowanych.
- Kod sieci 25000 i napięcie off-grid 50004 pozostają tylko do odczytu:
  brak dostatecznej walidacji dla konkretnego modelu i instalacji.
- Protokół baterii 52501 można edytować tylko dla marki 1, dla której PDF
  podaje wartości 0/1/2. Nie przypisujemy tych znaczeń innym markom.
- Nie przypisujemy opisów tabeli statusu EMS 53508 do statusu BMS 33002.
  Nieznane błędy BMS pokazują numery aktywnych bitów zamiast zgadywanych nazw.
- Brak testu zapisu na fizycznej Selfie; wyniki odnoszą się do lokalnego
  serwera Modbus TCP/RTU-over-TCP i testowego Home Assistant.

## Wyniki sprawdzenia

24 testy Python (w tym rzeczywiste platformy HA i usługi select/number/time),
10 testów karty JavaScript oraz kontrola Ruff — poprawne.
