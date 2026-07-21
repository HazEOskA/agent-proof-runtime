# Agent Proof Runtime

Agent Proof Runtime (APR) turns autonomous AI work into independently verifiable
execution evidence. It is a development sandbox and proof runtime, not a claim of
hardware-backed trust.

> **Proof before trust.** The agent performs the work. The runtime records the
> evidence. The verifier checks the proof. The human makes the decision.

Product doctrine:

- [Agent Proof Runtime Manifesto](docs/PROJECT_MANIFESTO.md)
- [Product Blueprint](docs/PRODUCT_BLUEPRINT.md)
- [Controlled live validation](docs/LIVE_VALIDATION.md)

## Live demo

- Mission Control: <https://agent-proof-runtime-production.up.railway.app>
- Health endpoint: <https://agent-proof-runtime-production.up.railway.app/health>
- 90-second public demo: <https://youtu.be/6UFQjGiVqbs>
- Hosted validation record: [docs/HOSTED_VALIDATION.md](docs/HOSTED_VALIDATION.md)
- Primary judge path: deterministic fixture mode with no API key or external network dependency.
- Hosted run storage may be ephemeral; the checked-in CLI path remains the reproducible source of truth.

## Supported platforms

- CLI, fixture runtime, verifier, and Tamper Lab: Python 3.11 or 3.12 on Windows, Linux, and macOS.
- Container deployment: Linux container; validated locally through Docker Desktop and publicly on Railway.
- gVisor backend: Linux Docker host with registered `runsc`; it fails closed when unavailable. Real `runsc` execution remains unvalidated.

## The problem

An agent can produce a useful artifact and a convincing activity log, but neither
proves that the artifact, policy result, or history remained unchanged. That gap is
especially costly in regulated workflows where an operator must explain what ran,
what was accepted, and what changed after the fact.

## The solution

APR accepts a strict mission manifest, asks a narrow provider for text artifact
proposals, enforces the artifact contract itself, runs deterministic acceptance
checks, and writes a versioned Proof Bundle. A separate verifier recalculates file
hashes, acceptance results, the event hash chain, RFC 6962-style Merkle root, and the
whole-bundle hash. GPT-5.6 proposes artifacts; it never decides cryptographic
validity.

```text
Mission Manifest
  -> strict validation
  -> fixture or OpenAI provider
  -> structured artifact proposal
  -> runtime policy enforcement
  -> controlled text materialization
  -> deterministic acceptance checks
  -> event hash chain + Merkle root
  -> Proof Bundle
  -> independent verification
  -> Mission Control + disposable Tamper Lab
```

APR preserves the legacy `apr demo`, MissionSpec v0.2, and v0.1/v0.2 Proof Bundle
verification paths.

## Mission Studio: seven agents, one proof boundary

Mission Studio accepts one constrained website brief and runs a fixed upstream
pipeline:

1. Mission Planner
2. Research Agent
3. Content Architect
4. HTML Builder
5. CSS Designer
6. Data Builder
7. QA Agent

The pipeline produces exactly four declared text artifacts:
`site/index.html`, `site/styles.css`, `site/data.json`, and
`studio/trace.json`. Those exact bytes are handed to APR's existing trust gate.
APR—not the agents—enforces paths, media types, file counts, and size limits,
runs 16 deterministic acceptance checks, writes the Proof Bundle, and invokes the
independent verifier. QA reviews the generated site but cannot issue
`LOCAL_VERIFIED`.

Fixture mode is deterministic, offline, and keyless. Live mode performs seven
sequential OpenAI Responses API calls with strict Structured Outputs and
`store=False`; it fails closed instead of replacing rejected live output with a
fixture template. The complete live Mission Studio path was validated on
2026-07-18 and returned `PASSED` / `LOCAL_VERIFIED` / `UNANCHORED`.

Implementation and claim boundaries are documented in
[Mission Studio](docs/MISSION_STUDIO.md) and
[Mission Studio live OpenAI mode](docs/MISSION_STUDIO_OPENAI.md).

## Install

Python 3.11 or 3.12 is supported.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The deterministic fixture path has no runtime dependencies and needs no secret.
Install the optional official OpenAI Python SDK only for a controlled live run:

```bash
python -m pip install -e '.[openai]'
```

## Judge quick start: no API key

```bash
apr mission validate examples/build-week-mission.json
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/build-week-demo
apr verify .runs/build-week-demo/proof-bundle.json
```

Expected result:

```text
Mission: PASSED
Proof:   LOCAL_VERIFIED
Anchor:  UNANCHORED
```

Fixture mode is deterministic, offline, CI-safe, and exercises the same proposal,
materialization, acceptance, event, and Proof Bundle contracts as live mode.

For the visual judge path, start Mission Control and run the preset Mission Studio
brief with the default **Fixture** provider:

```bash
apr mission-control
```

Open <http://127.0.0.1:8080>. No account, API key, or external service is required.

## Live GPT-5.6 mode

Live mode uses the official OpenAI Responses API with strict Structured Outputs,
`store=False`, and a configurable model whose default manifest value is `gpt-5.6`.
The runtime stores only provider name, requested/resolved model, response ID, token
counts, latency, and input/response hashes. It does not persist API keys, raw model
responses, hidden reasoning, or chain-of-thought.

```bash
# OPENAI_API_KEY must already be configured outside this repository.
APR_OPENAI_MODEL=gpt-5.6 apr run examples/build-week-mission.json \
  --provider openai \
  --output .runs/gpt-5-6-smoke
```

The direct artifact-provider path is **LIVE-VALIDATED**. On 2026-07-15, a
controlled local GPT-5.6 run completed with mission `PASSED`, proof
`LOCAL_VERIFIED`, and anchor `UNANCHORED`. Independent verification replayed all
five recorded events, and a persistence scan confirmed that the API key was absent
from every stored run file. The key was provided only through the current process
environment and removed immediately after the run.

The full seven-stage Mission Studio path is also **LIVE-VALIDATED**. On 2026-07-18,
seven sequential GPT-5.6 stages produced the four declared artifacts, reached QA and
APR without fixture fallback, passed all 16 deterministic checks, and returned
`PASSED` / `LOCAL_VERIFIED` / `UNANCHORED`. Disposable artifact and trace mutations
were detected while the original remained verified. These validations demonstrate
the provider integrations; they do not change APR's local, unsigned, externally
unanchored trust boundary.

## Mission Manifest v1

`apr.mission.v1` declares:

- identity, title, goal, provider, and model;
- exact relative artifact paths, media types, per-file and total byte limits;
- deterministic checks: `file_exists`, `file_count`, `contains_text`, `json_valid`,
  `json_required_keys`, and `maximum_size`;
- an analysis policy that forbids persisted reasoning.

The parser rejects unknown fields, duplicate JSON keys and paths, absolute paths,
`..`, unsafe media types, malformed checks, invalid limits, oversized manifests,
and fixture content outside the declared contract. Providers cannot submit shell
commands or arbitrary filesystem operations.

## Mission Control

```bash
apr mission-control
```

Open <http://127.0.0.1:8080>. The panel shows approved checked-in missions, fixture
or live provider, mission/proof/anchor status, safe provider metadata, acceptance
checks, artifacts and hashes, event replay, bundle hash, Merkle root, report, raw
bundle, and Tamper Lab.

`PORT` is honored, or use explicit options:

```bash
apr mission-control --host 127.0.0.1 --port 9090
```

The public UI cannot execute arbitrary commands or paths. State-changing requests
use a same-origin CSRF token; CSP, Host-header/DNS-rebinding, traversal, and symlink
guards remain enabled. Remote binding requires `--allow-remote` and provides no
user authentication, so use it only in a controlled demo environment.

Health check: `GET /health`.

## Tamper Lab

Tamper Lab copies a verified run into a temporary directory, changes only the copy,
invokes the independent verifier, returns the exact failure reasons, and then
deletes the copy. The original run is fingerprinted before and after.

```bash
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case artifact
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case event
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case metadata
```

Every case must return `FAILED` for the copy and preserve `LOCAL_VERIFIED` for the
original.

## Legacy and gVisor paths

```bash
apr demo --output .runs/legacy-demo
apr verify .runs/legacy-demo/proof-bundle.json
apr run missions/demo.json --output .runs/mission-v02
apr doctor --backend gvisor
```

`local-process` and the Build Week controlled-artifact runtime are
`development-only`; they are not boundaries for hostile code. The Docker + gVisor
adapter is fail-closed: if Docker does not report `runsc`, `apr doctor` reports
unavailable and execution does not silently fall back to `runc`.

The checked-in Docker image and containerized Mission Control flow were validated
on Windows Docker Desktop 4.74.0 with a Linux/amd64 engine: the container ran as
non-root user `uid=10001(apr)`, `/health` returned version `0.3.0`, Docker reported
`running / healthy`, and the full fixture/Tamper Lab judge path passed. Real gVisor
execution and `runsc` network containment remain unvalidated because `runsc` was
not installed in that environment.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite covers legacy compatibility, manifest strictness, artifact policy,
deterministic fixture reproducibility, mocked OpenAI Structured Outputs, absence of
secret persistence, independent acceptance reproduction, three tamper classes,
original-run preservation, Mission Control HTTP safety, health, CLI exit codes,
and gVisor fail-closed behavior. No live API call runs by default.

## Deployment

The checked-in `Dockerfile` starts Mission Control as a non-root user and includes
a `/health` probe. `railway.json` supplies a Railway-compatible Docker build and
start command. Fixture mode requires no secrets. For optional live mode, configure
`OPENAI_API_KEY` server-side and never expose it to the browser.

Run storage is local filesystem state and may be ephemeral on hosted platforms.
Persist `.runs` on an appropriate volume if evidence must survive restarts. Hosted
Mission Control is a single-operator demo, not a multi-tenant production control
plane.

## Trust boundaries

- `LOCAL_VERIFIED`: evidence is internally consistent and artifacts match.
- `FAILED`: proof structure, hashes, or independently reproduced evidence disagree.

A mission whose acceptance checks legitimately fail is reported as mission `FAILED`
with a `LOCAL_VERIFIED` proof when that failure was recorded consistently.
- `UNANCHORED`: no external log, signature, HSM, or independent host vouched for the
  bundle.
- `development-only`: do not run hostile code in this backend.

External append-only anchoring, out-of-host signing/HSM, inclusion proofs, TEE/TPM,
and in-toto mapping remain roadmap work. APR does not use `ANCHORED` until that
boundary really exists.

## Build Week provenance and collaboration

The repository `main` baseline before the final Build Week continuation was
`8bba7ed`. The preserved branch contains the original Codex implementation lineage
(`4a22da3` -> `9ff5152` -> `fcfb7d0` -> `f03fe35`) and connects it to the public
GitHub history through merge commit `1b51055`, without rewriting or force-pushing
either history.

The preserved continuation was merged into `main` through `2eabbd0`, followed by
the final demo-documentation merge `bc8e85c` and CSS artifact-ceiling fix `e0ffbd3`.
The resulting `main` contains Mission Studio, the live GPT-5.6 path, the v1
manifest/provider/proof path, Tamper Lab, security coverage, competition
documentation, product doctrine, and the public Railway deployment. The preserved
implementation checkpoints were not rewritten or force-pushed.

Human architectural decisions locked the product as sandbox-first, required honest
`UNANCHORED`/`development-only` labels, preserved backward compatibility, and chose
fixture-first judging without an API key. Codex implemented and tested the branch
under those constraints. GPT-5.6 is the optional runtime artifact-proposal provider;
it is not used as the verifier. The provider was live-validated in a controlled
local run after the original keyless Work implementation was complete.

See:

- [Project Manifesto](docs/PROJECT_MANIFESTO.md)
- [Product Blueprint](docs/PRODUCT_BLUEPRINT.md)
- [Controlled live validation](docs/LIVE_VALIDATION.md)
- [Seven-stage Mission Studio live validation](docs/MISSION_STUDIO_OPENAI.md)
- [Hosted deployment validation](docs/HOSTED_VALIDATION.md)
- [Build Week guide](docs/BUILD_WEEK.md)
- [Architecture Lock](docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md)
- [Before Build Week](docs/BEFORE_BUILD_WEEK.md)
- [Build Week changelog](docs/BUILD_WEEK_CHANGELOG.md)
- [Codex collaboration](docs/CODEX_COLLABORATION.md)
- [90-second demo script](docs/DEMO_SCRIPT.md)
- [Gap audit](docs/BUILD_WEEK_GAP_AUDIT.md)

## Read the book: *Proof Before Trust*

<a href="book/PROOF_BEFORE_TRUST.md">
  <img src="book/cover.svg" alt="Proof Before Trust — Engineering Verifiable Execution for Autonomous AI Agents" width="320">
</a>

The repository includes Bartosz Osiński's complete 32-chapter technical book about
APR's product architecture, evidence model, trust boundaries, validation record,
and roadmap.

- [Book overview and table of contents](book/README.md)
- [Read the complete assembled manuscript](book/PROOF_BEFORE_TRUST.md)
- [Review the repository evidence map](book/SOURCES.md)
