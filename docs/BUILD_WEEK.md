# Build Week — Codex Mission Control v1

Gałąź zgłoszeniowa: `build-week/codex-mission-control-v1`

## Jednozdaniowy opis

Agent Proof Runtime uruchamia zatwierdzoną misję agenta w świeżym środowisku i
zostawia rachunek wykonania, który niezależny validator potrafi przeliczyć bez
zaufania do werdyktu runtime'u.

## Przepływ demonstracyjny

```text
MissionSpec
    │
    ▼
Mission Control ──► istniejący Mission Runner ──► local-demo / Docker + gVisor
                                              │
                                              ▼
                                   artefakty + event hash chain
                                              │
                                              ▼
                                  Proof Bundle + Merkle root
                                              │
                                              ▼
                                    niezależny Validator
```

Mission Control jest adapterem operatora. Nie ma własnego runnera, formatu dowodu
ani alternatywnego validatora.

## Demo w 90 sekund

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
apr mission-control
```

1. Otwórz `http://127.0.0.1:8080`.
2. Uruchom `builtin-demo`.
3. Zobacz statusy `PASSED`, `LOCAL_VERIFIED` i `UNANCHORED`.
4. Otwórz raport i pokaż artefakt oraz łańcuch zdarzeń.
5. Zmień zawartość artefaktu w nowym katalogu `.runs/.../artifact/hello.txt`.
6. Kliknij `Sprawdź` — validator powinien zwrócić `FAILED`.

To pokazuje najważniejszą różnicę między zwykłym logiem a dowodem: zmiana wyniku po
fakcie zostaje wykryta.

## Stan wykonania

### Ukończone i uruchomione

- pionowy przebieg: misja → workspace → artefakt → test → bundle → validator,
- ścisły MissionSpec v0.2,
- JCS-safe profil kanonikalizacji dla obsługiwanych typów,
- SHA-256 event chain i Merkle root według algorytmu RFC 6962,
- niezależna weryfikacja bundle i plików artefaktów,
- statyczny raport operatora,
- fail-closed adapter Docker + gVisor,
- Mission Control v1 z historią, uruchamianiem i ponowną weryfikacją,
- testy manipulacji, traversal, symlinków, limitów i niedostępnego backendu.

### Zaimplementowane, ale wymagające bramki labowej

- realny run obrazu przez `runsc` na hoście Linux,
- fizyczne testy sieci, timeoutu, forka i wyczerpania zasobów pod gVisorem,
- zastąpienie placeholdera digestu w przykładzie prawdziwym `RepoDigest`.

Kod nie spada do `runc`, gdy `runsc` jest nieobecny. Brak hosta labowego oznacza
`OFFLINE`, a nie udawany sukces.

### Roadmapa, nie claim zgłoszenia

- zewnętrzny append-only anchor service,
- podpis kluczem poza hostem runtime lub PKCS#11/HSM,
- inclusion proof i status `ANCHORED`,
- TEE, TPM/measured boot oraz profil in-toto.

## Komendy akceptacyjne

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agent_proof_runtime mission validate missions/demo.json
PYTHONPATH=src python -m agent_proof_runtime run missions/demo.json --output /tmp/apr-build-week
PYTHONPATH=src python -m agent_proof_runtime verify /tmp/apr-build-week/proof-bundle.json
PYTHONPATH=src python -m agent_proof_runtime doctor --backend gvisor
```

Ostatnia komenda ma zwrócić błąd na maszynie bez Dockera i `runsc`. To oczekiwane
zachowanie fail-closed.

## Granica bezpieczeństwa panelu

- domyślny bind: `127.0.0.1`,
- operacje POST wymagają losowego tokenu osadzonego w stronie z tego samego originu,
- tylko manifesty z kontrolowanego katalogu mogą zostać uruchomione,
- publiczne pliki runu są ograniczone do raportu, Proof Bundle i `artifact/`,
- symlinki, `..`, ścieżki absolutne i niekanoniczne są odrzucane,
- panel nie jest wieloużytkownikowym systemem z logowaniem i nie powinien być
  wystawiany publicznie.
