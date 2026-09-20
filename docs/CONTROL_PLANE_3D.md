# APR 3D Control Plane

Immersyjny control plane dla Agent Proof Runtime. Świat 3D jest interfejsem;
DOM jest wyłącznie warstwą pomocniczą.

**APR pozostaje źródłem prawdy.** Frontend nie wykonuje pracy, nie ocenia jej
i nie wymyśla postępu. Renderuje wyłącznie to, co runtime faktycznie zapisał.

```text
3D FRONTEND
  -> AprClient            (istniejące endpointy Mission Control)
  -> RuntimeEventAdapter  (APR EVENT -> WORLD EVENT)
  -> WORLD STATE
  -> scena 3D
```

## Granica architektoniczna

| Warstwa | Lokalizacja | Odpowiedzialność |
| --- | --- | --- |
| Świat 3D | `frontend/src/world/` | render, kamera, ruch, efekty |
| Adapter runtime | `frontend/src/runtime/` | mapowanie zdarzeń APR na stan świata |
| Klient API | `frontend/src/api/` | wyłącznie istniejące route'y APR |
| Host statyczny | `src/agent_proof_runtime/control_plane.py` | serwowanie builda + wstrzyknięcie tokenu |

Python core nie zyskuje zależności od Node. `frontend/` jest osobnym
projektem źródłowym z własnym `package.json`.

## Uruchomienie

```bash
cd frontend
npm install
npm run build
cd ..
apr mission-control --missions-dir missions --runs-dir .runs
# http://127.0.0.1:8080/control-plane
```

Tryb deweloperski (Vite proxuje APR, więc przeglądarka pozostaje same-origin):

```bash
cd frontend
VITE_APR_TOKEN="<token z dokumentu /control-plane>" npm run dev
```

Katalog builda można wskazać zmienną `APR_CONTROL_PLANE_DIST`.

## Kontrakt zdarzeń

Frontend nie zmienia nazewnictwa w backendzie. Adapter mapuje rzeczywiste
zdarzenia APR na wewnętrzne zdarzenia świata:

| Zdarzenie APR | Zdarzenie świata | Efekt w scenie |
| --- | --- | --- |
| `studio.mission_accepted` | `MISSION_ACCEPTED` | Mission Stone przechodzi w RUNNING |
| `agent.{stage_id}.started` | `AGENT_STARTED` | stage dostaje stanowisko, agent do niego podchodzi |
| `agent.{stage_id}.completed` | `AGENT_COMPLETED` | stanowisko kończy pracę, pojawia się shard artefaktu |
| `handoff.{src}_to_{dst}` | `HANDOFF` | fizyczny transfer danych między stanowiskami |
| `apr.run.started` | `RUN_STARTED` | Proof Core przyjmuje run |
| `apr.contract_enforced` | `CONTRACT_ENFORCED` | wpis w logu świata |
| `apr.run.completed` | `RUN_COMPLETED` | **WYKONANIE: ZAKOŃCZONE, WERYFIKACJA: OCZEKUJE** |
| `verifier.completed` | `VERIFICATION_COMPLETED` | dopiero tutaj ustala się wynik dowodu |
| `studio.mission_failed` | `MISSION_FAILED` | świat przechodzi w FAILED |

## CLAIM ≠ PROOF

Status wykonania i status dowodu są osobnymi polami stanu i osobnymi
elementami UI. Po `apr.run.completed` świat pokazuje
`WYKONANIE: ZAKOŃCZONE` razem z `WERYFIKACJA: OCZEKUJE`.
Wynik dowodu ustawia wyłącznie `verifier.completed`.

## Cztery stanowiska, więcej etapów

Runtime ma dziś siedem etapów, świat ma cztery fizyczne stanowiska.
`RuntimeEventAdapter` przydziela aktywny etap do wolnego stanowiska i zwalnia
je po zakończeniu. Rola nad stanowiskiem pochodzi z `stage_id` zwróconego
przez runtime — nie jest zaszyta w scenie.

## Tempo odtwarzania

Runtime kończy run fixture szybciej, niż człowiek jest w stanie to zobaczyć.
Zdarzenia są kolejkowane i odtwarzane po jednym co ~260 ms. To decyzja
rendererska: runtime decyduje **co** się wydarzyło, renderer decyduje
**jak płynnie** to pokazać. Kolejka zawsze drenuje się do rzeczywistego stanu
i nigdy nie dodaje zdarzenia, którego APR nie zapisał.

## Polling

APR nie ma SSE ani WebSocketu. Control plane odpytuje:

- `GET /health` co 4 s — brak odpowiedzi to `RUNTIME OFFLINE`,
- `GET /api/studio/{id}` co 0,5 s — polling zatrzymuje się w stanie terminalnym,
- `GET /api/runs/{run_id}` raz, po ustaleniu wyniku weryfikacji.

## Klucze API

Klucz providera jest konfiguracją backendu (`OPENAI_API_KEY`). Frontend go nie
przyjmuje, nie wyświetla i nie zapisuje — ani w `localStorage`, ani w
`sessionStorage`, ani w URL, ani w repozytorium. Panel Senseia pokazuje jedynie
providera, model i stan połączenia.

Token żądania Mission Control jest wstrzykiwany do serwowanego dokumentu przez
runtime, tak samo jak dla istniejącego dashboardu, i nie jest nigdzie utrwalany.

## Poza zakresem Slice 1

OpenRouter, NVIDIA NIM, BYOK secret management, uniwersalny silnik misji,
dynamiczne narzędzia, wiele misji równolegle, konta i billing.

---

# SLICE 2 — GENERIC MISSION V1

Sensei przyjmuje dowolne zadanie tekstowe. Runtime projektuje plan, waliduje go,
wykonuje etapy i dopiero wtedy APR rozstrzyga, co zostało udowodnione.

```text
PROMPT
  -> planner (model albo deterministyczny fixture)
  -> GenericMissionPlanV1            walidacja, planner nie jest zaufany
  -> wygenerowany manifest apr.mission.v1
  -> etapy = realne wywołania modelu
  -> artefakty
  -> istniejący runtime, chain, Merkle, Proof Bundle
  -> niezależny weryfikator APR
  -> PROOF
```

Nie powstał drugi system dowodowy. Misja generyczna to zwykła misja
`apr.mission.v1` — tyle że jej manifest jest generowany z zatwierdzonego planu,
a nie pisany ręcznie.

## Co APR tutaj udowadnia

`verification_scope` w sesji i w artefakcie planu: `execution`,
`artifact_integrity`, `contract_acceptance`.

APR dowodzi, że:

- etap został wykonany i jest zapisany w łańcuchu zdarzeń,
- artefakt powstał i ma konkretny, zapisany hash,
- artefakt nie został zmieniony po wykonaniu (chain, Merkle root, bundle hash),
- zadeklarowane handoffy nastąpiły,
- deterministyczne warunki akceptacji zostały spełnione,
- Proof Bundle jest wewnętrznie spójny i przechodzi niezależną weryfikację.

## Czego APR tutaj NIE udowadnia

APR **nie** twierdzi, że odpowiedź modelu jest prawdziwa, poprawna merytorycznie
ani dobrej jakości. Nie ma tu LLM-as-a-judge i nie ma żadnego checku, który
prosiłby model o ocenę wyniku. `LOCAL_VERIFIED` oznacza integralność wykonania,
nie prawdziwość treści.

## Kontrakt planu

`GenericMissionPlanV1`, maksymalnie 4 etapy w tej wersji:

```json
{
  "version": "generic-mission-plan-v1",
  "title": "...",
  "goal": "...",
  "stages": [
    {
      "id": "analyze",
      "role": "ANALYST",
      "instruction": "...",
      "expected_output": {"type": "text"},
      "acceptance": [{"type": "artifact_present"}, {"type": "nonempty_text"}],
      "inputs": []
    }
  ]
}
```

Plan pochodzący od modelu jest walidowany przed wykonaniem: wersja, długości,
unikalne identyfikatory etapów, format roli, wspierany typ wyjścia, `inputs`
wskazujące wyłącznie wcześniejsze etapy oraz wyłącznie dozwolone checki.
Odrzucony plan kończy misję (`planner_contract_invalid`) i **nie** tworzy runu.

## Allowlista warunków akceptacji

Planner wybiera z zamkniętej listy i nie może wymyślić własnego checku:

| Check planu | Mapowanie na istniejący check runtime'u |
| --- | --- |
| `artifact_present` | `file_exists` |
| `nonempty_text` | `minimum_size` z `min_bytes: 1` |
| `min_length` | `minimum_size` |
| `json_parseable` | `json_valid` |
| `json_required_keys` | `json_required_keys` |

`minimum_size` to jedyny nowy typ checku dodany do rdzenia. Reszta reużywa
istniejących. Weryfikator odtwarza je niezależnie tym samym kodem.

## Role i stanowiska

Role pochodzą z planu (`ANALYST`, `CRITIC`, `REWRITER`, `REVIEWER` albo
`PLANNER`, `CODER`, `TESTER`, `VERIFIER` — cokolwiek zwróci runtime).
Etap `stages[i]` trafia na stanowisko `AGENT 0{i+1}`. Przy mniej niż czterech
etapach pozostałe stanowiska zostają `WOLNE`. Nic w scenie nie zna nazw ról.

## Handoffy

Krawędzie biorą się z `inputs` w planie, a nie z kolejności numerycznej.
Po ostatnim etapie runtime emituje `handoff.{ostatni}_to_apr`. Frontend używa
tego samego `RuntimeEventAdapter` co w Slice 1 — nie dodano hardcode pod misję.

## Providerzy

| Provider | Tryb | Sieć |
| --- | --- | --- |
| `fixture` | deterministyczny plan i deterministyczne etapy | brak |
| `openrouter` | realny planner i realne wykonanie etapów | HTTPS |

Bieg `fixture` **nie jest** biegiem providera. Służy testom i demonstracji bez
sieci i bez klucza; UI nazywa go deterministycznym fixture.

Konfiguracja OpenRoutera (wyłącznie po stronie serwera):

```bash
export OPENROUTER_API_KEY=...                       # tylko env, nigdy w repo
export APR_OPENROUTER_MODEL=vendor/model            # domyślnie openrouter/auto
export OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Adapter jest zbudowany na bibliotece standardowej — wybranie live providera nie
dodaje żadnej zależności runtime do pakietu. Brak klucza kończy misję
kategorią `provider_not_configured` **przed** jakimkolwiek wywołaniem.

## Klucze

Klucz nie trafia do frontendu, bundla, `localStorage`, `sessionStorage`, URL-a,
odpowiedzi API, komunikatu błędu, logu, Proof Bundle ani artefaktu. Komunikaty
błędów providera są budowane wyłącznie ze statusu HTTP i klasy wyjątku. Pokrywa
to osobny test szczelności sekretu.

Status providera w UI: `NOT_CONFIGURED`, `CONFIGURED`, `LAST_CALL_OK`, `ERROR`,
`RATE_LIMITED`, `AUTH_FAILED`. `CONFIGURED` oznacza obecność poświadczenia,
nigdy udanego wywołania — interfejs nie pokazuje `CONNECTED`.

## Kategorie błędów

`request_invalid`, `planner_invalid_json`, `planner_contract_invalid`,
`provider_not_configured`, `openrouter_auth_failed`, `openrouter_rate_limited`,
`openrouter_server_error`, `openrouter_timeout`, `openrouter_connection_failed`,
`openrouter_request_failed`, `stage_failed`, `runtime_io_failed`,
`runtime_failed`.

## Zgodność wsteczna

`verified_website_build` działa bez zmian — ten sam kontrakt żądania, te same
etapy, ten sam Proof Bundle. `POST /api/studio/start` przyjmuje oba typy misji:

```json
{"mission_type": "generic_v1", "prompt": "...", "provider": "fixture", "max_agents": 4}
{"mission_type": "verified_website_build", "brief": "...", "provider": "fixture"}
```

## Poza zakresem Slice 2

NVIDIA NIM, BYOK i UI do sekretów, Anthropic, Gemini, marketplace narzędzi,
automatyzacja przeglądarki, sandbox wykonania kodu, SSE, WebSocket,
wielu użytkowników, konta, billing. Generic mission z providerem `openai`
również nie wchodzi w ten slice — adapter bramki modelu obsługuje dziś
OpenRoutera.
