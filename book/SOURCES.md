# Repository Evidence Map

This book is derived exclusively from the active Agent Proof Runtime repository.
Paths below are relative to the repository root.

## Product doctrine

- `docs/PROJECT_MANIFESTO.md` — trust gap, evidence doctrine, human authority.
- `docs/PRODUCT_BLUEPRINT.md` — canonical thirty-two-section book order and product contract.
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` — locked Build Week implementation choices.
- `docs/ARCHITECTURE_LOCK_v0.1.md` and `docs/ARCHITECTURE_LOCK_v0.2.md` — preserved earlier contracts.
- `docs/ROADMAP.md` — staged development beyond the current local trust boundary.

## Implementation

- `src/agent_proof_runtime/mission_v1.py` — strict Mission Manifest v1 parser.
- `src/agent_proof_runtime/providers.py` — fixture and optional OpenAI provider boundary.
- `src/agent_proof_runtime/build_week_runtime.py` — proposal policy and controlled materialization.
- `src/agent_proof_runtime/acceptance.py` — deterministic acceptance evaluator.
- `src/agent_proof_runtime/canonical.py` — canonical serialization and SHA-256 helpers.
- `src/agent_proof_runtime/chain.py` — event construction and chain verification.
- `src/agent_proof_runtime/merkle.py` — RFC 6962-style Merkle construction.
- `src/agent_proof_runtime/validator.py` — version-aware independent verifier.
- `src/agent_proof_runtime/mission_control.py` — constrained HTTP control surface.
- `src/agent_proof_runtime/tamper_lab.py` — disposable tamper experiments.
- `src/agent_proof_runtime/gvisor.py` — fail-closed Docker + gVisor adapter.
- `src/agent_proof_runtime/cli.py` — operator command surface.

## Validation and provenance

- `docs/BUILD_WEEK.md` — competition path and demonstrated claims.
- `docs/BUILD_WEEK_GAP_AUDIT.md` — evidence-based delivery audit.
- `docs/LIVE_VALIDATION.md` — dated controlled GPT-5.6 provider validation.
- `docs/HOSTED_VALIDATION.md` — dated Railway Mission Control validation.
- `docs/BEFORE_BUILD_WEEK.md` — baseline capability history.
- `docs/BUILD_WEEK_CHANGELOG.md` — preserved implementation checkpoints.
- `docs/CODEX_COLLABORATION.md` — earlier environment-specific implementation record.

## Temporal claim rule

Some provenance documents capture an earlier moment. In particular,
`docs/CODEX_COLLABORATION.md` records the OpenAI provider as implemented but not
live-validated in the environment where that document was written. The later dated
record `docs/LIVE_VALIDATION.md` documents a successful controlled run on
2026-07-15. The book treats the later validation as the current provider status
while preserving the earlier document as accurate historical provenance.

No external source is required to understand or validate the product claims made
in this edition.
