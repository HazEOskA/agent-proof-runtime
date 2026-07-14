# Agent Proof Runtime

Eksperymentalna piaskownica dla agentów AI, która po wykonaniu zadania zostawia
nie tylko log, ale też **sprawdzalny rachunek wykonania** (`Proof Bundle`).

Pierwszy kamień milowy jest celowo mały:

```text
jeden agent -> świeży workspace -> artefakt -> test -> Proof Bundle -> niezależny validator
```

## Co już działa w v0.1

- świeży, automatycznie usuwany katalog roboczy dla każdej misji,
- proces agenta z oczyszczonym środowiskiem, limitem czasu i podstawowymi limitami zasobów,
- zebranie artefaktów bez dowiązań symbolicznych i bez wyjścia poza katalog runu,
- liniowy hash chain zdarzeń (SHA-256),
- korzeń Merkle zgodny z algorytmem RFC 6962,
- samowystarczalny `proof-bundle.json`,
- osobna komenda `verify`, która ponownie liczy cały dowód i hashe artefaktów,
- wykrywanie manipulacji w zdarzeniu, artefakcie i metadanych bundle,
- statyczny raport `report.html`, który można pokazać bez czytania JSON-a.

## Ważna granica bezpieczeństwa

Backend `local-process` jest **harnessem deweloperskim, nie granicą bezpieczeństwa**.
Nie blokuje sieci i nie chroni hosta przed złośliwym kodem. Bez zewnętrznej kotwicy
lub podpisu atakujący z pełną kontrolą hosta może przeliczyć cały dowód od nowa.

To świadoma decyzja v0.1. Następnym backendem izolacji będzie gVisor lub microVM,
a następną warstwą zaufania — zewnętrzna kotwica i klucz poza hostem runtime.

## Start w 60 sekund

Wymagany jest Python 3.11 lub nowszy. Projekt nie ma zależności runtime.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

apr demo --output .runs/first-run
apr verify .runs/first-run/proof-bundle.json
```

Otwórz `.runs/first-run/report.html`, aby zobaczyć raport operatora.

Można też uruchomić bez instalowania skryptu CLI:

```bash
PYTHONPATH=src python -m agent_proof_runtime demo --output .runs/first-run
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

## Dokumenty

- [Architecture Lock v0.1](docs/ARCHITECTURE_LOCK_v0.1.md) — zamrożony zakres,
  kontrakty kryptograficzne, przepływ i threat model.
- [Roadmap](docs/ROADMAP.md) — droga od lokalnego PoC do realnej izolacji i
  zewnętrznego zaufania.

## Statusy walidatora

- `LOCAL_VERIFIED` — bundle jest wewnętrznie spójny i artefakty pasują, ale dowód
  nie ma jeszcze zewnętrznej kotwicy ani podpisu.
- `FAILED` — validator wykrył co najmniej jedną niespójność.

Projekt nie używa statusu `ANCHORED`, dopóki naprawdę nie istnieje niezależny,
append-only rejestr po drugiej stronie granicy zaufania.
