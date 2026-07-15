# Part IV — The Integrity Core

## Chapter 13 — Event Model

Ordinary logs describe activity. APR events are structured inputs to an integrity
calculation. The difference is not that logs are useless; it is that a mutable list
of messages cannot by itself reveal removal, reordering, or modification.

Every protected event contains:

- a sequential index;
- an event type;
- structured input, output, and details;
- a hash of each structured section;
- the previous event's step hash;
- its own step hash.

The first event points to a fixed genesis value: a `sha256:` prefix followed by
thirty-two zero bytes expressed as hexadecimal. Later events point to the exact step
hash stored in their predecessor.

### Canonical bytes

Hashing JSON requires a deterministic representation. Whitespace, key order, and
number formatting can make semantically similar objects produce different byte
strings. APR uses an integer-safe subset of RFC 8785 identified as
`RFC8785-JCS-INTEGER-PROFILE-v1`.

The profile serializes objects with lexicographic UTF-16 key ordering, emits UTF-8,
rejects lone UTF-16 surrogates, accepts integers only within the IEEE-754 safe range
of plus or minus 9,007,199,254,740,991, and rejects floating-point values. These
restrictions trade broad JSON flexibility for stable cross-process hashing.

For event `i`, APR first calculates:

```text
I_i = SHA256(canonical(input_i))
O_i = SHA256(canonical(output_i))
D_i = SHA256(canonical(details_i))
```

The step payload binds the event index, type, those three hashes, and the previous
step hash:

```text
S_i = SHA256(canonical({
  step_index: i,
  type: type_i,
  input_hash: I_i,
  output_hash: O_i,
  details_hash: D_i,
  previous_step_hash: S_(i-1)
}))
```

The actual implementation hashes a canonical JSON object with named fields rather
than a positional tuple, but the dependency is the same.

### What the chain detects

If an event's input, output, or details change, its section hash changes. That
changes the step hash. The next event's `previous_step_hash` no longer points to the
recomputed value. Removing or reordering events also breaks sequential indices and
linkage. Adding unknown fields or deleting required fields fails exact schema checks.

The verifier performs these calculations from event content. It does not compare
only the stored step hashes to each other.

### Build Week event sequence

A fixture mission with two artifacts records five significant transitions:

1. `runtime.mission_started`;
2. `provider.artifact_proposal_received`;
3. one `runtime.artifact_materialized` event per artifact;
4. `runtime.acceptance_completed`.

The sequence is compact on purpose. An evidence stream should capture security- and
verification-relevant transitions without becoming a dump of every debug message.
Operational logs may remain useful outside the bundle, but verification facts need
stable structured semantics.

### Merkle aggregation

APR turns event step hashes into a Merkle root using RFC 6962-style domain
separation. An empty tree hashes the empty byte string. A leaf hashes the byte
`0x00` followed by the decoded step-hash bytes. An internal node hashes `0x01`
followed by its left and right child hashes. Non-power-of-two trees split at the
largest power of two smaller than the leaf count.

The linear chain and Merkle root are related but not identical. The chain makes
order and predecessor linkage explicit. The root gives a compact commitment to the
complete ordered leaf set and prepares the architecture for future inclusion-proof
work. The current bundle does not claim an external transparency log merely because
it has a Merkle root.

### Repository evidence

- `src/agent_proof_runtime/canonical.py`
- `src/agent_proof_runtime/chain.py`
- `src/agent_proof_runtime/merkle.py`
- `tests/test_chain_merkle.py`

## Chapter 14 — Proof Bundle

The Proof Bundle is APR's primary product artifact: a versioned, portable execution
receipt designed to remain useful outside the runtime and Mission Control.

Build Week uses `apr.proof-bundle.v1`. The repository's verifier also preserves
support for `apr.proof-bundle.v0.1` and `.v0.2`. Version dispatch is essential
because evidence semantics cannot be changed retroactively without invalidating old
receipts or, worse, interpreting them under rules they never claimed to satisfy.

### Bundle anatomy

The v1 bundle contains seven major evidence areas:

| Section | Purpose |
|---|---|
| `schema_version` | Selects the exact verification semantics. |
| `mission` | Stores the canonical manifest and its recomputable hash. |
| `provider` | Stores allowlisted provider metadata and interaction hashes. |
| `run` | Identifies the run, backend, security level, network policy, and timing. |
| `events` | Carries the ordered hash-linked execution record. |
| `artifacts` | Records relative paths, media types, sizes, and SHA-256 digests. |
| `acceptance` | Carries mission outcome and individual deterministic results. |
| `verification` | Records the runtime's claimed local status as a claim to check. |
| `integrity` | Declares canonicalization, algorithm, counts, Merkle root, bundle hash, and anchor status. |

The bundle stores the complete normalized Mission Manifest rather than only a
mission identifier. Portability requires enough context to understand what was
supposed to happen. It stores artifact metadata rather than embedding every file;
the verifier resolves referenced artifacts relative to the bundle's run directory.

### The whole-bundle hash

The bundle hash commits to the verification-relevant document. APR computes it from
a canonical representation that excludes the bundle-hash field itself according to
the versioned bundle logic. The verifier applies the same exclusion rule and
recomputes the digest.

This hash detects changes to critical metadata that artifact and event hashes alone
might not cover: mission fields, provider values, run properties, acceptance
records, event count, Merkle root, anchor status, or the claimed verification state.

A self-contained hash is not an external signature. If an attacker replaces the
document and recomputes the hash, a local verifier sees a consistent new bundle.
External anchoring or signing is required to prove that a particular historical
hash existed outside the attacker's control.

### Portable does not mean context-free

To re-verify a bundle, a recipient needs the bundle and its referenced artifact
tree. The verifier does not need the original Mission Control process or provider
connection. It also does not need the API key or raw model response. This is a
deliberate privacy and operational boundary: proof should contain what is necessary
for its claims, not every piece of sensitive execution state.

### Conservative status language

The bundle's anchor field is `UNANCHORED`. The runtime security level is
`development-only` for the controlled-artifact path. These values travel with the
evidence so that a copied bundle cannot be separated easily from its limitations.

The Proof Bundle is therefore not a certificate that the world should trust an
agent. It is a structured receipt that lets another process check precise execution
claims under a declared model.

### Repository evidence

- `src/agent_proof_runtime/bundle.py`
- `src/agent_proof_runtime/build_week_runtime.py`
- `src/agent_proof_runtime/validator.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` schemas

## Chapter 15 — Independent Verifier

The independent verifier is the component that turns APR from a recording system
into a verification system. Its foundational rule is simple:

> Never trust a status merely because the runtime wrote it.

The verifier receives the path to a Proof Bundle. It parses the JSON, identifies the
schema version, applies the exact supported shape, resolves the run directory, and
derives its own result. A successful runtime is not a prerequisite for a successful
verification; a faithfully recorded failed mission may still produce valid
evidence.

### Verification sequence

For a v1 bundle, the verifier performs a layered replay:

1. Validate top-level and nested key sets.
2. Validate supported schema and data types.
3. Recompute the canonical Mission Manifest hash.
4. Validate safe provider metadata shape and consistency.
5. Resolve each artifact under the run root.
6. Reject absolute paths, traversal, missing files, unknown files, and symlinks.
7. Re-read bytes and recompute size and SHA-256.
8. Validate event fields and sequential indices.
9. Recompute input, output, details, and step hashes.
10. Rebuild previous-step linkage.
11. Recompute the RFC 6962-style Merkle root.
12. Reproduce deterministic acceptance checks from the artifacts.
13. Compare reproduced results with recorded evidence and mission status.
14. Recompute the bundle hash.
15. Cross-check event counts, security labels, and other critical metadata.

Any mismatch contributes a concrete failure reason. The verifier should fail as a
result, not crash as an exception, when it receives corrupted evidence. The
repository records one illustrative hardening change: invalid UTF-8 introduced by
artifact tampering originally escaped as an exception; the boundary was changed to
return `FAILED`, and a regression test was added.

### Exact shapes matter

Unknown fields are not harmless in evidence formats. They may carry a second status
or an alternative interpretation ignored by one verifier and trusted by another.
APR uses exact key sets for supported schemas. Missing and unknown fields are
reported rather than silently normalized.

### Independence and shared deterministic logic

The verifier can reuse a pure deterministic acceptance evaluator without trusting
the runtime's stored output. Independence does not require rewriting every
mathematical rule in a different language. It requires independently reading the
source evidence and deriving the result rather than accepting the executor's
conclusion.

For stronger assurance, the long-term roadmap can add independently implemented
verifiers, published test vectors, and external execution. The current architecture
already makes that possible because the bundle is versioned and portable.

### Failure as useful output

A good verifier says more than `false`. It tells the operator that an artifact hash
mismatched, an event no longer pointed to its predecessor, the Merkle root differed,
the bundle hash was wrong, an acceptance record could not be reproduced, or a path
was unsafe. Precise error output supports audit, debugging, and incident response.

The verifier's authority is still bounded. It determines evidence integrity. It
does not determine whether the artifact is strategically wise, legally sufficient,
or ready to deploy. That decision belongs to the operator.

### Repository evidence

- `src/agent_proof_runtime/validator.py`
- `tests/test_validator_tampering.py`
- `tests/test_build_week_runtime.py`
- `docs/CODEX_COLLABORATION.md`

## Chapter 16 — Mission Control

Cryptographic evidence is valuable only when operators can understand and use it.
Mission Control provides a human-facing view over APR's existing runner and
verifier. It does not replace either component and does not invent a new source of
truth.

The interface exposes approved checked-in missions, provider selection, mission
status, proof status, anchor status, safe provider metadata, artifacts and hashes,
acceptance checks, event replay, bundle hash, Merkle root, generated report, raw
bundle, re-verification, and Tamper Lab. The central design rule is:

> Every security or execution claim in the interface must map to bundle evidence,
> verifier output, or runtime state with an explicit limitation.

### Thin adapter, shared semantics

Mission Control calls the same mission loader, runtime, and verifier used by the
CLI. A UI-only verification algorithm would risk divergence. A green badge derived
from server state instead of bundle replay would weaken the product's central claim.

The interface separates mission, proof, and anchor status. This prevents an
acceptance failure from being mistaken for evidence corruption and prevents local
integrity from being presented as external anchoring.

### Constrained public surface

The HTTP application is a small standard-library Python service with static frontend
assets. It allows checked-in or explicitly approved missions rather than arbitrary
host paths. Public execution defaults to fixture mode. Optional OpenAI execution
uses server-side configuration; credentials never reach browser code.

The server implements controls relevant to its scope:

- same-origin CSRF tokens for state changes;
- restrictive Content Security Policy;
- Host-header and DNS-rebinding checks;
- request-size limits;
- normalized run and artifact paths;
- traversal and symlink rejection;
- constrained file serving;
- explicit remote-binding opt-in.

Remote binding requires `--allow-remote` and still does not create user
authentication. The project therefore describes hosted Mission Control as a
single-operator demo, not a multi-tenant production control plane.

### Operational honesty

The public Railway validation recorded one operational edge case. After an
automatic redeploy, a stale browser tab held a CSRF token from the previous process
and received `request token is missing or invalid`. Reloading obtained the new token
and restored normal operation. The control was not disabled to make the demo pass.

This is the kind of detail evidence-oriented products should preserve. A successful
hosted validation includes the constraints and observed recovery behavior, not only
a screenshot of the healthy state.

### Mission Control is not the proof

An operator can download or inspect the bundle and verify it through the CLI. If
Mission Control disappears, the receipt still has meaning. This portability keeps
the user interface in its proper role: explanation and operation, not monopoly over
truth.

### Repository evidence

- `src/agent_proof_runtime/mission_control.py`
- `src/agent_proof_runtime/mission_control_ui.py`
- `tests/test_mission_control.py`
- `tests/test_mission_control_build_week.py`
- `docs/HOSTED_VALIDATION.md`
