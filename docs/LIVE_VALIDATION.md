# Controlled Live Validation

Date: 2026-07-15

This record documents one controlled local validation of the optional OpenAI
provider after the deterministic fixture path, test suite, verifier, Mission
Control, Tamper Lab, and Docker judge path were already complete.

## Environment and scope

- Provider: official OpenAI provider
- Requested model: `gpt-5.6`
- Mission: `examples/build-week-mission.json`
- Secret delivery: current PowerShell process environment only
- Persisted run path: `.runs/gpt-5-6-smoke-20260715-112455`
- External anchor: none

The API key value is not recorded in this document, the repository, the Proof
Bundle, the report, or any run artifact.

## Observed result

```text
Mission: PASSED
Proof:   LOCAL_VERIFIED
Anchor:  UNANCHORED
Bundle:  .runs/gpt-5-6-smoke-20260715-112455/proof-bundle.json
Report:  .runs/gpt-5-6-smoke-20260715-112455/report.html
```

Independent verification returned:

```text
Proof:   LOCAL_VERIFIED
Mission: PASSED
Anchor:  UNANCHORED
Events:  5
```

A recursive exact-value scan of every persisted file in the run directory found no
copy of the API key. The process-level `OPENAI_API_KEY` and `APR_OPENAI_MODEL`
environment variables were removed immediately after the run.

## Claim boundary

This validates that the optional GPT-5.6 provider can complete the declared mission,
produce a structured artifact proposal, traverse the same runtime and proof
contracts as fixture mode, and produce evidence that the independent verifier
accepts.

It does not create external non-repudiation, remote anchoring, hostile-code
isolation, gVisor validation, HSM/TEE guarantees, or a production security
certification. The correct trust labels remain `LOCAL_VERIFIED` and `UNANCHORED`.
