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
