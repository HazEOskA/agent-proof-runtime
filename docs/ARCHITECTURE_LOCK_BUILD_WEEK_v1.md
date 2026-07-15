# Architecture Lock — Build Week v1

Status: locked for the competition vertical slice.

## Product contract

Agent Proof Runtime converts autonomous AI work into independently verifiable
execution evidence.

```text
Mission Manifest
  -> Manifest Validation
  -> Provider
  -> Structured Artifact Proposal
  -> Runtime Policy Enforcement
  -> Controlled Artifact Materialization
  -> Deterministic Acceptance Checks
  -> Hashed Event Chain
  -> Merkle Root
  -> Proof Bundle
  -> Independent Verification
  -> Mission Control
  -> Tamper Lab
```

## Locked implementation choices

- One Python package, standard library at runtime.
- Optional official `openai` SDK only for live provider selection.
- Strict JSON objects with unknown-field and duplicate-key rejection.
- RFC 8785 integer-safe canonicalization profile already used by legacy bundles.
- SHA-256 linear event chain and RFC 6962-style domain-separated Merkle tree.
- Text artifacts only, exact allowlisted relative POSIX paths, no shell.
- Deterministic acceptance allowlist only; no subprocess or hosted shell checks.
- Mission Control remains a thin adapter over the same runner and verifier as CLI.
- Tamper Lab copies an existing verified run and never mutates the original.

## Schemas

- Mission: `apr.mission.v1`
- Proof Bundle: `apr.proof-bundle.v1`
- Legacy read compatibility: `apr.proof-bundle.v0.1` and `.v0.2`

The v1 bundle includes the canonical manifest and hash, safe provider metadata,
artifact contract, artifact hashes, acceptance evidence, event chain, Merkle root,
bundle hash, runtime verification claim, and anchor status. The verifier recomputes
all applicable evidence and does not trust the claim.

## Provider boundary

Both fixture and OpenAI providers return exactly:

```text
ArtifactProposal { artifacts: [{ path, media_type, content }] }
ProviderMetadata  { provider, requested_model, resolved_model, response_id,
                    token_usage, latency_ms, input_hash, response_hash,
                    implementation_status }
```

The fixture is deterministic and offline. The OpenAI adapter uses the Responses API
with strict JSON Schema Structured Outputs and `store=False`. It is optional and is
selected only by manifest or `--provider openai`. `OPENAI_API_KEY` is read by the SDK
adapter at request time and is never added to a manifest, event, report, or bundle.

Hidden reasoning, chain-of-thought, raw responses, SDK objects, and arbitrary model
metadata are outside the persistence contract.

## Runtime policy

The manifest fixes exact paths and media types. The runtime independently enforces:

- canonical relative paths and exact contract membership;
- required artifacts and duplicate rejection;
- allowed text/media types;
- maximum files, per-file bytes, and total bytes;
- fresh destination and exclusive file creation;
- no symlinks and no arbitrary command execution.

## Acceptance policy

Allowed checks are `file_exists`, `file_count`, `contains_text`, `json_valid`,
`json_required_keys`, and `maximum_size`. The verifier reads the materialized files
and reproduces each result. GPT-5.6 has no role in this verdict.

## Threat and trust boundary

Detected without trusting the runtime's stored status:

- file content/size/hash changes;
- event input/output/details/type or chain changes;
- manifest, provider, run, acceptance, Merkle, or bundle metadata changes;
- traversal, absolute paths, unknown files, duplicate paths, and symlinks.

Not solved in this vertical slice:

- a hostile administrator who replaces files and recomputes the entire local bundle;
- external append-only anchoring or out-of-host signatures;
- malicious code execution isolation in the controlled-artifact backend;
- multi-tenant authentication and authorization;
- hardware identity, TEE, TPM, HSM, or in-toto conformance.

Those limitations are why the only truthful proof/anchor/security labels are
`LOCAL_VERIFIED`, `FAILED`, `UNANCHORED`, and `development-only`.
