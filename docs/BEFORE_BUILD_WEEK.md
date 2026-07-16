# Before Build Week

This document records repository provenance without inventing calendar history.

## Declared baseline

The public GitHub `main` baseline before final Build Week publication points to
`8bba7ed`. The original implementation lineage was preserved separately and then
connected to that public history without rewriting either side. The technical sandbox
baseline in that preserved lineage was built in three commits:

| Commit | Capability present at that checkpoint |
|---|---|
| `9ff5152` | Local development sandbox, event hash chain, Merkle root, Proof Bundle v0.1, independent verifier, report, initial tests |
| `fcfb7d0` | Strict MissionSpec v0.2, Docker + gVisor fail-closed adapter, Proof Bundle v0.2 compatibility |
| `f03fe35` | First Mission Control, run history, re-verification, report/artifact access, CSRF/CSP/Host/path/symlink protections |

`f03fe35` is the immutable starting checkpoint for the final Build Week
continuation. It remains an ancestor; it was not amended, rebased, squashed, or
reconstructed.

## Not present at `f03fe35`

- `apr.mission.v1` artifact-proposal manifest;
- deterministic fixture and optional OpenAI providers sharing one contract;
- controlled provider artifact materialization;
- independently reproduced acceptance evidence;
- Proof Bundle `apr.proof-bundle.v1`;
- disposable artifact/event/metadata Tamper Lab;
- `/health`, Dockerfile, Railway configuration, and competition documentation.

## Human decisions carried into Build Week

- The product is sandbox-first; proof evidence is an additional differentiator.
- Backward compatibility is mandatory.
- `LOCAL_VERIFIED`, `FAILED`, `UNANCHORED`, and `development-only` remain honest.
- A fixture must demonstrate the complete path without a secret or network call.
- A model may propose artifacts but cannot issue host commands or decide validity.
- No gVisor, Docker, HSM, anchoring, or live-provider success may be claimed without
  a real test.
