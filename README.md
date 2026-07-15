# Agent Proof Runtime

Eksperymentalna piaskownica dla agentów AI, która po wykonaniu zadania zostawia
nie tylko log, ale też **sprawdzalny rachunek wykonania** (`Proof Bundle`).

Pierwszy kamień milowy jest celowo mały:

```text
jeden agent -> świeży workspace -> artefakt -> test -> Proof Bundle -> niezależny validator
```

## Co już działa

- świeży, automatycznie usuwany katalog roboczy dla każdej misji,
- proces agenta z oczyszczonym środowiskiem, limitem czasu i podstawowymi limitami zasobów,
- zebranie artefaktów bez dowiązań symbolicznych i bez wyjścia poza katalog runu,
- liniowy hash chain zdarzeń (SHA-256),
- korzeń Merkle zgodny z algorytmem RFC 6962,
- samowystarczalny `proof-bundle.json`,
- osobna komenda `verify`, która ponownie liczy cały dowód i hashe artefaktów,
- wykrywanie manipulacji w zdarzeniu, artefakcie i metadanych bundle,
- statyczny raport `report.html`, który można pokazać bez czytania JSON-a.
- ścisły `MissionSpec v0.2`, dzięki któremu workload nie jest związany z APR,
- backend gVisor, który działa fail-closed i nigdy nie spada po cichu do `runc`,
- `apr doctor`, który sprawdza, czy Docker naprawdę zarejestrował runtime `runsc`.
- lokalny **Mission Control**, który uruchamia istniejące manifesty, pokazuje historię
  runów i ponownie odpala niezależny validator bez dodawania drugiej ścieżki wykonania.

## Ważna granica bezpieczeństwa

Backend `local-process` jest **harnessem deweloperskim, nie granicą bezpieczeństwa**.
Nie blokuje sieci i nie chroni hosta przed złośliwym kodem. Bez zewnętrznej kotwicy
lub podpisu atakujący z pełną kontrolą hosta może przeliczyć cały dowód od nowa.

To świadoma granica backendu `local-demo`. Dla wrogiego kodu przeznaczony jest
backend `gvisor`: blokuje sieć, używa read-only root filesystem, pustych capabilities,
limitów zasobów i kopii katalogu źródłowego. Proof nadal pozostaje lokalny i
niepodpisany — zewnętrzna kotwica oraz klucz poza hostem są kolejną warstwą zaufania.

## Start w 60 sekund

Wymagany jest Python 3.11 lub nowszy. Projekt nie ma zależności runtime.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

apr mission validate missions/demo.json
apr run missions/demo.json --output .runs/first-run
apr verify .runs/first-run/proof-bundle.json
```

Otwórz `.runs/first-run/report.html`, aby zobaczyć raport operatora.

## Mission Control

Panel demonstracyjny działa bez zależności frontendowych i korzysta dokładnie z tego
samego `run_mission()` oraz `verify_bundle()` co CLI:

```bash
apr mission-control
```

Następnie otwórz `http://127.0.0.1:8080`. Panel:

- wykrywa wyłącznie manifesty JSON z katalogu `missions`,
- nie przyjmuje dowolnej komendy ani dowolnej ścieżki,
- uruchamia jedną misję naraz,
- pokazuje dostępność `runsc`, status misji, dowodu i kotwicy,
- pozwala otworzyć raport, Proof Bundle i zadeklarowane artefakty,
- wymaga losowego tokenu dla operacji zmieniających stan i blokuje path traversal
  oraz dowiązania symboliczne.

Domyślnie serwer nasłuchuje tylko na loopbacku. Zdalny bind wymaga jawnego
`--allow-remote`; panel nie zapewnia uwierzytelniania użytkowników, dlatego ta opcja
jest przeznaczona wyłącznie do kontrolowanego środowiska demonstracyjnego.

Można też uruchomić bez instalowania skryptu CLI:

```bash
PYTHONPATH=src python -m agent_proof_runtime mission validate missions/demo.json
PYTHONPATH=src python -m agent_proof_runtime run missions/demo.json --output .runs/first-run
PYTHONPATH=src python -m agent_proof_runtime verify .runs/first-run/proof-bundle.json
```

## Test manipulacji

Po poprawnym runie zmień zawartość artefaktu:

```bash
printf 'tampered\n' > .runs/first-run/artifact/hello.txt
apr verify .runs/first-run/proof-bundle.json
```

Validator powinien zakończyć się kodem `1` i statusem `FAILED`.

## Testy projektu

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## MissionSpec v0.2

MissionSpec rozdziela system agenta od piaskownicy. Minimalna misja deklaruje backend,
workload, limity, politykę sieci i politykę artefaktów. Parser odrzuca nieznane pola,
duplikaty kluczy, floaty, ścieżki z `..` oraz obrazy bez digestu.

```bash
apr mission validate missions/demo.json
apr run missions/demo.json
```

`local-demo` przyjmuje wyłącznie wbudowanego workera. Nie istnieje opcja uruchomienia
dowolnej lokalnej komendy, więc przypadkowe użycie nie omija izolacji.

## Backend gVisor

Wymagany jest host Linux z Dockerem i zarejestrowanym runtime `runsc`.

```bash
apr doctor --backend gvisor
```

Jeżeli Docker lub `runsc` nie są dostępne, komenda kończy się błędem **przed**
utworzeniem katalogu runu. Nie ma fallbacku do zwykłego Dockera.

Przykład znajduje się w `missions/gvisor-python.example.json`. Digest złożony z zer
jest celowym placeholderem: przed uruchomieniem trzeba zastąpić go prawdziwym
`RepoDigest` obrazu już znajdującego się na hoście. Runtime używa `--pull=never`.

## Dokumenty

- [Architecture Lock v0.1](docs/ARCHITECTURE_LOCK_v0.1.md) — zamrożony zakres,
  kontrakty kryptograficzne, przepływ i threat model.
- [Architecture Lock v0.2](docs/ARCHITECTURE_LOCK_v0.2.md) — MissionSpec oraz
  fail-closed backend Docker + gVisor.
- [Roadmap](docs/ROADMAP.md) — droga od lokalnego PoC do realnej izolacji i
  zewnętrznego zaufania.
- [Build Week](docs/BUILD_WEEK.md) — stan zgłoszenia, demonstracja i uczciwe granice.

## Statusy walidatora

- `LOCAL_VERIFIED` — bundle jest wewnętrznie spójny i artefakty pasują, ale dowód
  nie ma jeszcze zewnętrznej kotwicy ani podpisu.
- `FAILED` — validator wykrył co najmniej jedną niespójność.

Projekt nie używa statusu `ANCHORED`, dopóki naprawdę nie istnieje niezależny,
append-only rejestr po drugiej stronie granicy zaufania.
