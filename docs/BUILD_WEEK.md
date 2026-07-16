# OpenAI Build Week — Agent Proof Runtime

Competition branch: `build-week/codex-mission-control-v1`

## Submission sentence

Agent Proof Runtime converts autonomous AI work into independently verifiable
execution evidence: controlled artifacts, deterministic acceptance checks, a hashed
event chain, a Merkle root, and a self-contained Proof Bundle.

## Why it matters

Agent observability says what a system logged. APR demonstrates whether the declared
artifact, acceptance evidence, and execution history still match what was recorded.
It makes tampering visible without asking the model or UI to judge itself.

## Judge path

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
apr run examples/build-week-mission.json --provider fixture --output .runs/judge-demo
apr verify .runs/judge-demo/proof-bundle.json
apr mission-control
```

Open <http://127.0.0.1:8080>, select the verified run, inspect its evidence, and run
artifact, event, and metadata Tamper Lab cases. Each copy must fail while the
original remains verified.

## Fixture versus live

Fixture mode is the primary reproducible judging path. It has no key, network, or
third-party dependency but traverses the same provider result, runtime policy,
acceptance, event, Proof Bundle, verifier, report, Mission Control, and Tamper Lab
contracts as live mode.

The optional official OpenAI provider uses Responses API Structured Outputs and a
configurable `gpt-5.6` default. The provider is **LIVE-VALIDATED**: on 2026-07-15 a
controlled local run completed with mission `PASSED`, proof `LOCAL_VERIFIED`, anchor
`UNANCHORED`, five independently replayed events, and no API key found in persisted
run files. The key existed only in the current process environment and was removed
after the run. The live result validates the provider integration, not external
anchoring or non-repudiation.

## Demonstrated claims

- Strict versioned Mission Manifest and Proof Bundle extension.
- Deterministic fixture and same-shape optional OpenAI provider.
- Controlled live GPT-5.6 provider validation with no secret persistence.
- Model output constrained to artifact proposals; no arbitrary host commands.
- Runtime-enforced relative paths, media types, file counts, and byte limits.
- Six deterministic check types with independent reproduction.
- SHA-256 event chain, RFC 6962-style Merkle root, and whole-bundle hash.
- Backward-compatible v0.1/v0.2 verification.
- Mission Control evidence view and three disposable tamper cases.
- HTTP path/Host/CSRF/CSP/symlink protections and `/health`.
- Docker image and full containerized judge path validated as non-root and healthy.
- No-secret persistence tests and absent-key fail-closed behavior.

## Honest limitations

- The local proof is unsigned and externally unanchored.
- The controlled-artifact runtime is `development-only`, not hostile-code isolation.
- A fully privileged host attacker can replace and recompute local evidence.
- Mission Control is a single-operator demo without multi-user authentication.
- Hosted run storage may be ephemeral.
- The Docker image and Mission Control path were locally validated, but real gVisor
  execution remains unvalidated because `runsc` was not installed.
- HSM, TEE, TPM, append-only anchoring, inclusion proof, and in-toto are roadmap.

## Acceptance commands

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
apr demo --output /tmp/apr-legacy-demo
apr verify /tmp/apr-legacy-demo/proof-bundle.json
apr run examples/build-week-mission.json --provider fixture --output /tmp/apr-build-week
apr verify /tmp/apr-build-week/proof-bundle.json
apr tamper-lab /tmp/apr-build-week/proof-bundle.json --case artifact
apr tamper-lab /tmp/apr-build-week/proof-bundle.json --case event
apr tamper-lab /tmp/apr-build-week/proof-bundle.json --case metadata
apr doctor --backend gvisor
```

The last command is expected to report unavailable on a machine without Docker and
registered `runsc`; there is no fallback to `runc`.
