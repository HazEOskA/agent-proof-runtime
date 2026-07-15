# Part II — Goals, Boundaries, and Contracts

## Chapter 5 — Product Goals

Agent Proof Runtime has a long-term direction, but its current value comes from a
complete vertical slice. A small system that actually runs, records, verifies, and
fails visibly is more useful than a broad trust architecture made mostly of future
claims.

The Build Week goal can be drawn as one continuous chain:

```text
Mission Manifest
-> Provider
-> Structured Artifact Proposal
-> Policy Enforcement
-> Artifact Materialization
-> Acceptance Checks
-> Event Chain
-> Merkle Root
-> Proof Bundle
-> Independent Verification
-> Mission Control
-> Tamper Lab
```

Each arrow matters. Removing the manifest turns the run into an unbounded prompt.
Removing policy gives provider output direct authority. Removing deterministic
checks leaves only subjective evaluation. Removing the chain or artifact hashes
makes later modification harder to detect. Removing the independent verifier leaves
the executor judging itself. Removing the Tamper Lab makes the integrity claim less
understandable to a user.

### Functional goals

The current product must support versioned mission definitions and remain usable
without external secrets. That is why the fixture provider is a first-class
component rather than an emergency fallback. A judge, developer, or CI runner can
exercise the complete evidence path deterministically.

The optional live provider must share the same boundary. It may change the content
proposal, response identifier, token usage, and latency, but it must not create a
second policy model or a weaker verification path. Fixture and live execution meet
at the `ArtifactProposal` and safe provider metadata contracts.

The system must constrain artifacts, execute only allowlisted objective checks,
preserve older bundle verification, provide both CLI and Mission Control access,
and make evidence portable outside the interface. These are product goals because
they shape the user experience, not only internal engineering.

### Trust goals

APR must distinguish at least four independent questions:

1. Did execution complete operationally?
2. Did the declared acceptance checks pass?
3. Is the recorded evidence internally consistent?
4. Has an external authority anchored or signed that evidence?

One green status cannot answer all four. A provider can complete while acceptance
fails. Acceptance can fail while the proof remains valid. A proof can be locally
valid while externally unanchored. A hosted UI can be healthy while the execution
backend remains development-only.

This separation creates honest composability. A later signing service can add an
external trust result without redefining `LOCAL_VERIFIED`. A stronger execution
backend can improve isolation without changing the meaning of an artifact digest.

### Usability goals

Verification infrastructure fails as a product if only its authors can operate it.
The repository therefore defines a judge path that should complete within minutes:
run a checked-in mission, inspect evidence, verify it, tamper with a copy, and see a
precise failure. The CLI provides a transparent automation surface; Mission Control
provides legibility.

The result is not "maximum security in one week." It is a complete, defensible
execution-evidence loop with clear seams for stronger future components.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 5
- `docs/BUILD_WEEK.md`

## Chapter 6 — Explicit Non-Goals

Trust products are often damaged by their adjectives. Words such as secure,
verified, tamper-proof, isolated, and compliant can suggest guarantees far beyond
the implemented boundary. APR uses explicit non-goals to prevent that drift.

The Build Week system does not claim secure execution of arbitrary hostile code.
Its controlled-artifact path writes allowlisted text artifacts and never turns
provider output into shell commands. The older local-process harness is useful for
development but is not a kernel security boundary. A Docker container improves
packaging and process separation, but Docker alone is not proof against hostile
workloads.

The repository contains a fail-closed Docker + gVisor adapter. Fail-closed means
that when Docker does not report the `runsc` runtime, APR reports the backend as
unavailable rather than silently falling back to `runc` while claiming gVisor
protection. Simulated tests validate the adapter logic. Real gVisor execution is
still unvalidated in the recorded environment because `runsc` was not installed.

APR also does not provide external non-repudiation. A bundle hash detects changes
only when compared within the declared trust model. If an attacker has full control
of the host, can replace artifacts and bundle, and can recompute all local hashes,
the current system has no external witness that preserves the original value. That
is why every current receipt is `UNANCHORED`.

Other explicit non-goals include:

- public transparency logging;
- trusted external timestamps;
- HSM-backed signing;
- TEE, TPM, or remote-attestation guarantees;
- multi-tenant production isolation;
- automatic regulatory certification;
- proof of complete semantic correctness;
- proof that model reasoning was correct;
- storage of hidden reasoning or chain-of-thought;
- blockchain anchoring;
- autonomous deployment to production;
- automatic business approval.

These exclusions are not a confession that the product lacks purpose. They are a
map of the claim boundary. The delivered system can still detect accidental or
unauthorized modification of protected evidence within the local model. It can
still make provider output safer by constraining authority. It can still reproduce
objective checks. It can still create a portable record that a future external
anchor may sign.

Non-goals also reduce attack surface. The Build Week hosted path does not execute
model-generated shell commands, install packages, or accept arbitrary host paths.
It does not need to solve general remote code execution because its provider
contract is deliberately limited to text artifact proposals. Scope becomes a
security mechanism.

The practical rule is simple:

> Never promote a roadmap component into a present-tense guarantee before a real
> implementation and validation record exists.

This rule applies even when code exists. An adapter may be implemented but not
validated against the real runtime. A provider may be unit-tested with a fake
client but not yet observed in a controlled live call. A deployment file may exist
without a successful public health check. APR's documents preserve those temporal
distinctions.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 6
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` threat and trust boundary
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 7 — Canonical Product Objects

APR is organized around six canonical objects. Clear objects reduce ambiguity
between intent, proposal, side effect, evidence, and judgment.

### 1. Mission Manifest

The Mission Manifest is a versioned declaration of what should happen and what is
permitted. It contains mission identity, title, goal, provider and model requests,
an artifact contract, bounded limits, deterministic acceptance checks, and analysis
policy. The normalized manifest is hashed before provider execution.

The manifest is not merely configuration. It is the pre-execution contract against
which later behavior is interpreted.

### 2. Artifact Proposal

The provider returns an `ArtifactProposal`: a structured collection of proposed
text artifacts. Each item includes a relative path, media type, and content. The
proposal is untrusted input. It becomes useful only after parsing and policy checks.

This object prevents a provider response from being confused with a host action.
The model proposes; the runtime disposes.

### 3. Materialized Artifact

A Materialized Artifact is a file that passed the contract and was written inside
the controlled run directory. Its record includes path, media type, size, and
SHA-256 digest. The bytes on disk—not the provider's description—are the object the
verifier later re-hashes.

### 4. Event Record

An Event Record captures a significant transition in canonical form. The event is
linked to its predecessor and contains hashes of relevant inputs, outputs, and
details. Events form an ordered execution account rather than an unstructured log.

### 5. Proof Bundle

The Proof Bundle is the portable receipt. Version `apr.proof-bundle.v1` carries the
canonical mission and its hash, provider metadata, events, artifacts, acceptance
evidence, verification context, integrity roots, claimed runtime status, and anchor
state. Older v0.1 and v0.2 bundles remain supported by version-aware verification.

The bundle is the product's primary evidence artifact. Mission Control visualizes
it, but the interface is not required to verify it.

### 6. Verification Result

The Verification Result is the independent verdict produced by replaying the
supported integrity rules. It includes a status and exact reasons when checks fail.
It is not stored success being echoed back to the user.

### Object relationships

The six objects create a chain of authority:

```text
Manifest authorizes a bounded proposal surface
Proposal is filtered into materialized artifacts
Events record important transitions
Bundle packages the evidence
Verifier derives a result from bundle + artifacts
Operator decides what the verified evidence means for action
```

This separation avoids a common design error: storing one large "run result" object
that mixes intent, provider output, runtime action, evidence, and approval. When
those concepts are collapsed, it becomes difficult to say which fields are claims,
which are observations, and which must be recomputed.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 7
- `src/agent_proof_runtime/mission_v1.py`
- `src/agent_proof_runtime/providers.py`
- `src/agent_proof_runtime/validator.py`

## Chapter 8 — Mission Manifest

Every verifiable run begins before the provider is called. The Mission Manifest
freezes the contract that gives later evidence meaning.

APR's Build Week manifest uses schema version `apr.mission.v1`. Conceptually, it
defines:

```text
schema_version
mission_id
title
goal
provider
model
artifact_contract
limits
acceptance_checks
analysis_policy
```

The exact implementation is intentionally strict. The parser rejects unknown
top-level and nested fields instead of ignoring them. It rejects duplicate JSON
keys because a document whose meaning changes between parsers cannot be a stable
contract. It rejects duplicate artifact paths, absolute paths, traversal segments,
malformed POSIX-relative paths, unsupported media types, invalid integer limits,
oversized input, malformed check structures, and fixture content that falls outside
the declared contract.

Strictness serves two purposes. First, it blocks accidental ambiguity. A misspelled
field should fail visibly rather than silently removing a control. Second, it makes
canonical hashing meaningful. Two systems should not accept subtly different
interpretations of the same JSON text.

### Artifact authority

The manifest defines exact artifact entries and global limits. A provider cannot
create an additional file because it seems helpful. It cannot change a `.json`
contract to executable content. It cannot write `../outside.txt`, an absolute host
path, or a duplicate target. It cannot exceed the maximum file count, per-file byte
ceiling, or total byte budget.

This is capability design expressed as data. The provider receives authority only
over the files explicitly named in the contract.

### Acceptance before execution

Acceptance checks are also declared before the provider acts. That prevents the
system from moving the goalposts after seeing the output. The current allowlist is
small and deterministic. Each check has a stable identifier, type, target or
parameters, expected value, and later observed result.

The manifest does not attempt to encode every human expectation. A bounded machine
check should be used only when its semantics are objective. Subjective quality stays
with human review rather than being disguised as a deterministic verdict.

### Analysis policy

APR explicitly prevents hidden reasoning and chain-of-thought from entering the
persistence contract. The manifest can state whether a bounded reasoning summary is
allowed, but raw hidden reasoning, SDK internals, and model traces remain outside
the Proof Bundle. This protects secrets and avoids treating unverifiable internal
narrative as execution evidence.

### Manifest identity

After validation and normalization, the manifest is canonicalized and hashed. That
hash binds the later bundle to the exact contract used for execution. Editing a
title, goal, provider, artifact rule, limit, or check changes the identity. The
verifier recomputes the hash rather than trusting the stored value.

The manifest therefore answers three questions before autonomy begins:

1. What is expected?
2. What is permitted?
3. How will objective acceptance be evaluated?

An autonomous mission that cannot answer those questions cannot produce a precise
execution proof.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 8
- `src/agent_proof_runtime/mission_v1.py`
- `tests/test_build_week_manifest.py`
