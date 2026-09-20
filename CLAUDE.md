# Agent Proof Runtime — working notes

## What this repository is

APR turns agent work into independently verifiable execution evidence. The
proof pipeline is the product:

```text
mission manifest -> provider output -> runtime enforcement
  -> deterministic checks -> event chain + Merkle root
  -> Proof Bundle -> independent verification
```

`CLAIM != PROOF`. Execution status and verification status are separate
everywhere: in the runtime, in the API and in the UI.

## Invariants — do not break these

- **The proof core never imports anything cloud-specific.** `validator.py`,
  `chain.py`, `merkle.py`, `canonical.py` and `bundle.py` stay free of
  provider SDKs, cloud SDKs and network calls.
- **Zero mandatory runtime dependencies.** `pyproject.toml` keeps
  `dependencies = []`. Live providers are reached over the standard library or
  through an optional extra, never by adding a required package.
- **One proof system.** A new mission type generates an `apr.mission.v1`
  manifest and reuses the existing runtime. Never add a parallel proof format.
- **No fake execution.** No timer, animation or frontend state may stand in for
  a runtime event. If the backend is unreachable the world says so.
- **Verification is earned.** Only `verifier.completed` sets a proof status.
  `apr.run.completed` means execution finished and proof is pending.
- **Deterministic acceptance only.** Checks come from a closed allowlist. No
  LLM-as-a-judge, ever.
- **Secrets are server-side.** API keys live in the process environment. They
  never reach the frontend, a bundle, an artifact, a log or an error message.

## Cloud posture — portable across GCP, Azure and AWS

APR is built to deploy to **all three** clouds. No vendor lock-in; the customer
picks the cloud, not the codebase.

Today the runtime is already portable: one container, port from `PORT`, a
`/health` endpoint, no cloud SDKs anywhere in `src/`.

Rules:

- Cloud-specific material lives in `deploy/<gcp|azure|aws>/` and in thin
  adapters behind an interface. It never leaks into the core.
- Anything cloud-shaped (object storage, secret stores, queues) gets an
  interface first and at least a local implementation, so the default path
  needs no cloud at all.
- A deployment guide names the equivalent service on each cloud rather than
  assuming one provider.

Service equivalents:

| Concern | GCP | Azure | AWS |
| --- | --- | --- | --- |
| Serverless container | Cloud Run | Container Apps | App Runner |
| Image registry | Artifact Registry | ACR | ECR |
| Build | Cloud Build | ACR Tasks | CodeBuild |
| Secrets | Secret Manager | Key Vault | Secrets Manager |
| Object storage | GCS | Blob Storage | S3 |

Known portability gaps, unresolved by design and not yet scheduled:

1. `.runs` is local disk, so Proof Bundles do not survive a restart on any
   serverless platform. Needs an evidence store with per-cloud adapters, or an
   explicit decision to stay ephemeral.
2. Mission Studio sessions live in process memory, which blocks horizontal
   scaling everywhere.
3. The server is a single-threaded `http.server` with one global mission lock,
   so every platform must be configured with a concurrency of 1.
4. Provider credentials come from environment variables only; per-cloud secret
   stores are not wired up.

## Layout

```text
src/agent_proof_runtime/   Python runtime, verifier, Mission Control, model gateway
frontend/                  React + three.js + @react-three/fiber (own package.json)
tests/                     unittest suite
docs/                      architecture locks and guides
missions/ examples/        mission manifests
```

The Python runtime never depends on Node. `frontend/` is a separate source
project; the built bundle is served by `control_plane.py`.

## Commands

```bash
# tests (no install needed)
PYTHONPATH=src python3 -m unittest discover -s tests

# frontend
cd frontend && npm ci && npm run build

# run everything locally
python -m pip install -e .
apr mission-control --missions-dir missions --runs-dir .runs
# http://127.0.0.1:8080/control-plane
```

The served bundle is located through `APR_CONTROL_PLANE_DIST`; an installed
package cannot find it by walking up from its own file.

## Conventions

- Work happens on a feature branch. Do not touch `main`, and do not open a pull
  request unless asked.
- Report outcomes with evidence: real run ids, real hashes, real test output.
  Never write DONE without it.
