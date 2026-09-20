# Deployment portability — GCP, Azure, AWS

APR is deployed as one container. The codebase carries no cloud SDK and makes
no cloud API call, so the same image runs on all three major clouds without an
application change. This document records that decision and what still stands
in the way of it.

## Why the runtime is already portable

- `pyproject.toml` declares `dependencies = []`
- nothing under `src/` imports `boto3`, `google-cloud-*` or `azure-*`
- the server binds `0.0.0.0` and reads its port from `PORT`
- `/health` returns a JSON body with HTTP 200
- the only state is a runs directory passed on the command line

## Container contract

| Item | Value |
| --- | --- |
| Port | `PORT`, default `8080` |
| Health check | `GET /health` |
| Start command | `apr mission-control --host 0.0.0.0 --allow-remote` |
| Front-end bundle | `APR_CONTROL_PLANE_DIST=/app/frontend/dist` |
| Provider credential | `OPENROUTER_API_KEY` (optional, server-side only) |
| Concurrency | **1** — single-threaded server with one global mission lock |
| Memory | 2 GiB is comfortable; the image carries the built bundle |

`--allow-remote` is required on every managed platform, because the runtime
refuses a non-loopback bind without it.

## Service equivalents

| Concern | GCP | Azure | AWS |
| --- | --- | --- | --- |
| Serverless container | Cloud Run | Container Apps | App Runner |
| Image registry | Artifact Registry | ACR | ECR |
| Managed build | Cloud Build | ACR Tasks | CodeBuild |
| Secrets | Secret Manager | Key Vault | Secrets Manager |
| Object storage | GCS | Blob Storage | S3 |
| Identity for the service | Service account | Managed identity | Task role |

Azure Container Apps is the closest analogue to Cloud Run: a container, scale
to zero and immutable revisions. App Runner is the closest on AWS; ECS Fargate
is the fallback when finer networking control is needed.

## Architectural rule

Cloud-specific material belongs in `deploy/<gcp|azure|aws>/` and behind thin
adapters. The proof core — `validator.py`, `chain.py`, `merkle.py`,
`canonical.py`, `bundle.py` — never imports a cloud library. Any cloud-shaped
capability gets an interface and a local implementation first, so the default
path runs with no cloud at all.

This is what keeps APR verifiable on a laptop, in CI and in three clouds with
the same code.

## Open portability gaps

These are known and deliberately unresolved. None of them is scheduled.

1. **Evidence is not durable.** `.runs` is local disk, and every serverless
   platform gives an ephemeral filesystem, so Proof Bundles vanish on restart.
   Fixing it means an evidence store with GCS, Blob Storage and S3 adapters, or
   an explicit decision to keep runs ephemeral and export bundles instead.
2. **Sessions are in process memory.** Mission Studio state does not survive a
   restart and is not shared between instances, which blocks horizontal scaling
   on every platform.
3. **Concurrency is pinned to 1.** The server is a single-threaded
   `http.server` holding one global mission lock. Every platform must be
   configured accordingly; raising it requires a real concurrency design.
4. **Secrets come only from the environment.** Wiring a per-cloud secret store
   is not done.
