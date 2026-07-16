# Agent Proof Runtime — Product Blueprint

**Status:** Product Blueprint v0.1 — Candidate for Lock  
**Project:** Agent Proof Runtime  
**Product principle:** Proof before trust  
**Primary category:** Developer Tools  
**Initial release profile:** Build Week Mission Control v0.2

---

## 1. Executive Summary

Agent Proof Runtime is an execution-evidence layer for autonomous AI systems.

It accepts a declarative mission, invokes a deterministic fixture or an optional live model provider, enforces a controlled artifact contract, executes deterministic acceptance checks, records a cryptographically linked event stream, produces a portable Proof Bundle, and allows a separate verifier to independently determine whether the evidence is internally consistent.

The product does not attempt to prove that an AI agent made the best decision.

It proves narrower and more defensible claims:

- the declared mission was recorded,
- the runtime processed a specific provider response,
- only permitted artifacts were materialized,
- deterministic checks produced specific results,
- recorded artifacts match their cryptographic digests,
- recorded events form a valid hash chain,
- the declared Merkle root and bundle hash can be independently recomputed,
- later modification of protected evidence can be detected.

Agent Proof Runtime separates four responsibilities:

1. **The Mission Manifest defines the contract.**
2. **The provider proposes the output.**
3. **The runtime enforces policy and produces evidence.**
4. **The verifier independently evaluates evidence integrity.**

Mission Control visualizes the result, but the portable Proof Bundle remains the primary evidence artifact.

---

## 2. Product Definition

### 2.1 One-sentence definition

> Agent Proof Runtime converts autonomous agent activity into independently verifiable execution evidence.

### 2.2 Product promise

A user can submit an agent mission and receive:

- the resulting artifacts,
- a structured execution timeline,
- deterministic acceptance results,
- cryptographic integrity metadata,
- a portable Proof Bundle,
- an independent verification result.

### 2.3 Core product question

> What happened, what evidence was produced, and can another process independently verify the integrity of that evidence?

### 2.4 Primary user experience

The shortest complete user journey is:

```text
Select safe mission
        ↓
Run with fixture or live provider
        ↓
Inspect generated artifacts
        ↓
Review acceptance checks
        ↓
Inspect event timeline and hashes
        ↓
Verify Proof Bundle independently
        ↓
Modify a disposable copy in Tamper Lab
        ↓
Observe independent verification fail
```

---

## 3. Target Users

### 3.1 Initial users

Agent Proof Runtime initially serves:

- developers building autonomous agents,
- teams developing coding agents,
- agentic workflow engineers,
- AI infrastructure teams,
- AI QA and evaluation engineers,
- security-conscious automation teams,
- technical auditors reviewing agent execution.

### 3.2 Future users

Potential later profiles include:

- regulated AI operators,
- financial technology teams,
- healthcare automation teams,
- public-sector technology providers,
- compliance and governance teams,
- organizations requiring signed execution receipts,
- multi-agent platform operators.

These future users do not change the Build Week scope.

---

## 4. User Roles

### 4.1 Mission Author

Defines:

- mission goal,
- provider policy,
- artifact contract,
- execution limits,
- deterministic acceptance checks,
- evidence-retention policy.

The Mission Author does not control the verifier’s result.

### 4.2 Operator

Starts the mission, reviews evidence, inspects artifacts, runs verification, and decides whether to accept the outcome.

The Operator remains the final authority.

### 4.3 Provider

Produces a structured artifact proposal.

The provider may be:

- a deterministic fixture,
- OpenAI GPT-5.6,
- a future compatible adapter.

The provider is not trusted to enforce runtime policy or validate cryptographic evidence.

### 4.4 Runtime

Validates the mission, invokes the provider, enforces policy, materializes allowed artifacts, executes deterministic checks, records events, and creates the Proof Bundle.

### 4.5 Independent Verifier

Reads the Proof Bundle and referenced artifacts and recomputes the integrity decision.

It must not trust the runtime’s stored success status.

### 4.6 Judge or Auditor

Runs a predefined mission, reviews the result, verifies the bundle, and uses the Tamper Lab to observe failure detection.

---

## 5. Product Goals

### 5.1 Build Week goals

The Build Week version must demonstrate one complete vertical slice:

```text
Mission Manifest
→ Provider
→ Structured Artifact Proposal
→ Policy Enforcement
→ Artifact Materialization
→ Acceptance Checks
→ Event Chain
→ Merkle Root
→ Proof Bundle
→ Independent Verification
→ Mission Control
→ Tamper Lab
```

### 5.2 Functional goals

The system must:

- support declarative, versioned mission definitions,
- operate without external API keys through a fixture provider,
- optionally support GPT-5.6 through the OpenAI API,
- constrain provider output through an artifact contract,
- execute only allowlisted deterministic checks,
- preserve compatibility with existing v0.1 Proof Bundles,
- independently detect protected evidence manipulation,
- provide a clear local Mission Control interface,
- remain usable through the CLI without the interface,
- produce portable evidence outside the original runtime.

### 5.3 Trust goals

The system must clearly distinguish:

- execution success,
- acceptance-check success,
- local evidence verification,
- external anchoring status,
- backend security level.

---

## 6. Explicit Non-Goals

The Build Week version does not claim to provide:

- secure execution of arbitrary hostile code,
- kernel-enforced network isolation in local-process mode,
- production-grade multi-tenant isolation,
- remote non-repudiation,
- a public transparency log,
- trusted timestamps,
- hardware-backed signing,
- remote attestation,
- full semantic correctness of generated artifacts,
- automatic business approval,
- regulatory certification,
- proof that a model’s reasoning was correct,
- storage or exposure of hidden model reasoning,
- blockchain anchoring,
- autonomous deployment to production.

A successful Proof Bundle does not prove that the resulting artifact is useful, ethical, secure, or commercially correct.

---

## 7. Canonical Product Objects

Agent Proof Runtime is built around six canonical objects.

### 7.1 Mission Manifest

A versioned declaration of:

- what should happen,
- what may be produced,
- which limits apply,
- how objective acceptance will be evaluated,
- which provider is requested,
- which evidence may be retained.

### 7.2 Artifact Proposal

A structured provider response describing proposed artifacts.

It is data, not executable authority.

### 7.3 Materialized Artifact

A file accepted by runtime policy and written into the controlled run directory.

### 7.4 Event Record

A canonical, hash-linked record of an important execution transition.

### 7.5 Proof Bundle

A versioned portable receipt containing the mission identity, evidence records, artifact metadata, acceptance evidence, integrity roots, and verification-relevant metadata.

### 7.6 Verification Result

An independently derived result containing:

- status,
- checks performed,
- exact failure reasons,
- trust-boundary labels.

---

## 8. Mission Manifest

### 8.1 Purpose

The Mission Manifest freezes the contract before execution.

It prevents the provider or runtime from silently redefining:

- the goal,
- the permitted output surface,
- execution limits,
- acceptance conditions.

### 8.2 Required conceptual fields

A Build Week manifest should contain:

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

### 8.3 Manifest requirements

The manifest must:

- use a supported schema version,
- contain a unique mission identifier,
- use relative artifact paths,
- define finite limits,
- contain only supported acceptance-check types,
- reject unknown top-level fields,
- reject duplicated target paths,
- reject malformed policy structures,
- reject unsafe or oversized input,
- be hashable through canonical serialization.

### 8.4 Safe example

The repository should contain at least one checked-in mission that:

- requires no secret,
- produces a small deterministic result,
- completes quickly,
- demonstrates multiple acceptance checks,
- is safe to expose through Mission Control.

### 8.5 Mission immutability

The normalized mission hash must be recorded before provider execution.

Any later change to the mission should produce a different hash.

---

## 9. Provider Architecture

### 9.1 Provider interface

All providers must implement one narrow conceptual contract:

```text
Validated Mission
        ↓
Structured Artifact Proposal
+ Safe Provider Metadata
```

### 9.2 Fixture provider

The fixture provider is a first-class product component, not a fake fallback.

It must:

- require no API key,
- return deterministic output for the same normalized mission,
- exercise the same proposal parser,
- exercise the same artifact policy,
- exercise the same acceptance engine,
- produce the same class of evidence metadata,
- work in CI and judge environments.

Fixture provider success demonstrates runtime correctness independently of external availability.

### 9.3 OpenAI provider

The OpenAI provider must:

- use the supported official OpenAI interface,
- request structured output,
- use an environment-configurable model,
- default to GPT-5.6 where available,
- return artifact proposals rather than host commands,
- fail clearly when `OPENAI_API_KEY` is absent,
- never fall back silently to a different provider,
- never persist secrets or authorization headers.

### 9.4 Safe provider metadata

The runtime may retain:

- provider identifier,
- requested model,
- resolved model,
- response identifier,
- token usage,
- latency,
- input hash,
- normalized response hash,
- provider status.

The runtime must not retain:

- API keys,
- authentication headers,
- secret environment variables,
- hidden reasoning,
- chain-of-thought,
- internal safety traces,
- unrelated raw environment data.

### 9.5 Provider failure semantics

Provider failure must be distinguishable from:

- invalid manifest,
- artifact-policy rejection,
- acceptance-check failure,
- verifier failure.

---

## 10. Structured Artifact Proposal

### 10.1 Purpose

The provider proposes files. It does not receive direct authority to write arbitrary host paths.

### 10.2 Conceptual proposal shape

Each proposal item should contain fields such as:

```text
relative_path
artifact_type
media_type
content
explanation
```

### 10.3 Proposal rules

The proposal parser must reject:

- absolute paths,
- traversal segments,
- empty paths,
- duplicate paths,
- unsupported types,
- oversized content,
- malformed structured output,
- executable instructions presented as runtime commands.

### 10.4 No arbitrary command execution

The Build Week hosted path must not transform model output into:

- shell commands,
- package installation,
- arbitrary subprocess invocation,
- host filesystem access,
- dynamic interpreter execution.

Future execution backends may support stronger capabilities behind stronger isolation profiles. They are not part of the initial hosted flow.

---

## 11. Artifact Contract

### 11.1 Purpose

The artifact contract defines the maximum authority granted to the provider.

### 11.2 Enforced constraints

The runtime must enforce:

- relative paths only,
- allowed path patterns or explicit paths,
- maximum file count,
- maximum per-file bytes,
- maximum total bytes,
- allowed artifact or media types,
- no symbolic links,
- no path traversal,
- no writes outside the run workspace,
- no duplicate final paths.

### 11.3 Materialization sequence

```text
Parse proposal
        ↓
Normalize paths
        ↓
Validate against contract
        ↓
Check count and byte limits
        ↓
Create controlled directories
        ↓
Write artifacts
        ↓
Re-read artifacts
        ↓
Compute digests
        ↓
Record evidence
```

### 11.4 Artifact identity

Each recorded artifact should include:

- relative path,
- byte size,
- media or artifact type,
- SHA-256 digest,
- corresponding materialization event,
- optional contract rule that authorized it.

---

## 12. Acceptance Engine

### 12.1 Purpose

The acceptance engine performs deterministic checks defined before execution.

### 12.2 Initial check allowlist

The Build Week profile may support:

- `file_exists`
- `file_count`
- `contains_text`
- `json_valid`
- `json_required_keys`
- `maximum_size`

### 12.3 Check properties

Each check must be:

- declared in the Mission Manifest,
- deterministic,
- bounded,
- safe to execute,
- represented in the evidence,
- associated with a clear pass/fail result,
- reproducible without consulting the model.

### 12.4 Check evidence

Each result should contain:

- check identifier,
- check type,
- normalized parameters or their hash,
- target artifact where relevant,
- pass/fail result,
- safe observed value,
- exact failure reason,
- event reference.

### 12.5 Acceptance limitations

Acceptance checks validate objective requirements.

They do not establish:

- semantic quality,
- legal correctness,
- business suitability,
- absence of all vulnerabilities,
- compliance with unstated expectations.

---

## 13. Event Model

### 13.1 Purpose

Events provide an ordered execution record whose integrity can be independently recomputed.

### 13.2 Candidate event types

The runtime may record events such as:

```text
mission.received
mission.validated
provider.started
provider.completed
provider.failed
proposal.validated
artifact.materialized
acceptance.started
acceptance.completed
bundle.created
verification.completed
mission.completed
mission.failed
```

Existing v0.1 event semantics remain supported.

### 13.3 Event integrity

Each protected event must participate in:

- canonical serialization,
- input/output/details hashing where defined,
- previous-step hash linkage,
- step hash calculation,
- Merkle construction.

### 13.4 Event ordering

The verifier must detect:

- event mutation,
- broken previous-hash references,
- event removal,
- event reordering where chain semantics require order,
- incorrect event counts,
- incorrect Merkle roots.

---

## 14. Proof Bundle

### 14.1 Purpose

The Proof Bundle is the portable execution receipt.

### 14.2 Core sections

A Build Week bundle should contain:

```text
schema_version
run
mission
provider
events
artifacts
acceptance
verification_context
integrity
```

Exact field names may preserve existing implementation conventions.

### 14.3 Required evidence

The bundle should expose enough information to verify:

- normalized mission hash,
- provider metadata consistency,
- artifact-contract identity,
- artifact digests,
- acceptance evidence,
- event-chain integrity,
- event Merkle root,
- bundle-level integrity hash,
- declared anchor status.

### 14.4 Bundle hash

The bundle hash must be derived from a canonical representation excluding only the bundle-hash field itself or another explicitly versioned exclusion set.

The canonicalization profile must be documented.

### 14.5 Backward compatibility

The verifier must:

- continue supporting valid v0.1 bundles,
- dispatch validation according to schema version,
- reject unknown incompatible versions clearly,
- avoid silently applying new semantics to old receipts.

---

## 15. Independent Verifier

### 15.1 Independence principle

The verifier must derive its own decision.

It may read evidence created by the runtime, but it must not trust the runtime’s stored final status.

### 15.2 Verification sequence

The verifier should independently:

1. parse the bundle,
2. validate the schema version,
3. validate required and permitted fields,
4. resolve artifact paths safely,
5. reject absolute paths and traversal,
6. reject symbolic links,
7. recompute artifact hashes,
8. recompute event hashes,
9. recompute the event chain,
10. recompute the Merkle root,
11. recompute the bundle hash,
12. cross-check critical metadata,
13. validate acceptance evidence where reproducible,
14. produce an independent result.

### 15.3 Verification statuses

The initial product uses:

```text
LOCAL_VERIFIED
FAILED
UNANCHORED
```

`LOCAL_VERIFIED` does not imply an external trust anchor.

### 15.4 Failure reporting

A failed verification should identify concrete causes such as:

- artifact digest mismatch,
- missing artifact,
- unsafe artifact path,
- event hash mismatch,
- broken previous-step hash,
- Merkle-root mismatch,
- bundle-hash mismatch,
- critical metadata inconsistency,
- unsupported schema version,
- invalid acceptance evidence.

---

## 16. Mission Control

### 16.1 Purpose

Mission Control makes technical evidence understandable without replacing the underlying verifier.

### 16.2 Required views

The Build Week interface should provide:

- project explanation,
- current trust-boundary warning,
- safe mission selection,
- provider indicator,
- mission execution controls,
- mission status,
- proof status,
- anchor status,
- event timeline,
- artifact list,
- artifact digests,
- acceptance-check results,
- bundle hash,
- Merkle root,
- safe provider metadata,
- report access,
- bundle access,
- independent re-verification,
- Tamper Lab.

### 16.3 Interface truth rule

Every security or execution claim displayed in Mission Control must map to:

- bundle evidence,
- verifier output,
- runtime state with clearly stated limitations.

The interface must not invent stronger statuses.

### 16.4 Hosted safety profile

The public interface may execute only:

- checked-in missions,
- explicitly allowlisted safe missions,
- fixture runs by default,
- optional live-provider runs under server-side configuration.

It must not accept arbitrary host paths or shell commands.

---

## 17. Tamper Lab

### 17.1 Purpose

Tamper Lab demonstrates that integrity failure is observable rather than theoretical.

### 17.2 Required scenarios

The Build Week version should support:

1. artifact content modification,
2. event data modification,
3. critical metadata modification.

### 17.3 Copy-on-tamper rule

Tamper Lab must:

- create a disposable copy,
- never modify the original valid run,
- execute the independent verifier,
- return `FAILED`,
- show the precise reason,
- identify the tampered copy separately.

### 17.4 Demonstration outcome

The user should be able to compare:

```text
Original run: LOCAL_VERIFIED
Tampered copy: FAILED
```

This is a core demo moment.

---

## 18. CLI Product Surface

### 18.1 Legacy compatibility

Existing commands such as:

```bash
apr demo
apr verify
```

must continue working.

### 18.2 Mission execution

The product should expose a command similar to:

```bash
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/build-week-demo
```

### 18.3 Mission Control

The interface should start through a command such as:

```bash
apr mission-control
```

or a compatible `apr serve` alias.

### 18.4 Diagnostics

Backend diagnostics may expose:

```bash
apr doctor --backend gvisor
```

When gVisor is unavailable, the command must report that fact.

It must not silently substitute `runc` while claiming gVisor protection.

### 18.5 Exit-code classes

The CLI should distinguish:

- successful execution,
- invalid user input or manifest,
- provider failure,
- artifact-policy failure,
- acceptance failure,
- verification failure,
- operational startup failure.

---

## 19. HTTP Surface

### 19.1 Initial server profile

Mission Control remains a small single-process Python application with static frontend assets.

### 19.2 Required operations

The HTTP layer may provide:

- health status,
- safe mission listing,
- safe mission execution,
- run listing,
- run details,
- independent re-verification,
- report retrieval,
- Proof Bundle retrieval,
- constrained artifact retrieval,
- disposable tamper actions.

### 19.3 Security controls

The server should preserve or implement:

- CSRF protection for state changes,
- restrictive Content Security Policy,
- Host validation,
- DNS-rebinding resistance,
- path normalization,
- traversal prevention,
- symlink rejection,
- constrained content serving,
- safe error responses,
- finite request sizes,
- no arbitrary command execution.

### 19.4 Health endpoint

A lightweight `/health` endpoint should support local checks and platform deployment probes.

---

## 20. Repository Architecture

### 20.1 Architecture principle

Do not introduce distributed infrastructure before the product requires it.

### 20.2 Build Week structure

```text
Single Python package
├── CLI
├── Mission validation
├── Runtime
├── Provider adapters
├── Artifact policy
├── Acceptance engine
├── Event integrity
├── Proof Bundle builder
├── Independent verifier
├── Mission Control server
└── Static Mission Control frontend
```

### 20.3 Source-of-truth principle

GitHub is the canonical project history after authenticated publication.

Portable Git bundles may be used as preservation artifacts when the implementation environment cannot push safely.

### 20.4 Dependency principle

Prefer:

- standard library capabilities,
- narrow dependencies,
- explicit interfaces,
- deterministic tests,
- small operational surface.

Avoid unnecessary framework expansion.

---

## 21. Execution Backends

### 21.1 Local-process backend

The local-process backend remains:

```text
development-only
```

It may provide:

- fresh workspaces,
- environment reduction,
- resource limits where available,
- timeout enforcement,
- controlled built-in execution.

It is not a secure hostile-code boundary.

### 21.2 gVisor backend

gVisor is a stronger roadmap or experimental backend.

The product must distinguish:

- implementation present,
- runtime detected,
- runtime tested,
- runtime unavailable.

No successful gVisor claim may be made without a real Linux Docker + `runsc` validation.

### 21.3 Future backends

Potential future backends include:

- microVMs,
- Firecracker,
- remote isolated workers,
- sandboxed container platforms.

They must conform to the same evidence contracts rather than redefining Proof Bundle semantics.

---

## 22. Deployment Blueprint

### 22.1 Competition deployment

The preferred initial deployment profile is:

```text
Container image
        ↓
Railway or controlled Linux host
        ↓
Mission Control server
        ↓
Fixture provider enabled
        ↓
Optional OpenAI provider via server-side environment
```

### 22.2 Secret handling

`OPENAI_API_KEY` must exist only in the backend environment.

It must never appear in:

- repository files,
- browser code,
- bundle fields,
- reports,
- logs,
- downloaded artifacts,
- screenshots,
- documentation examples containing real values.

### 22.3 Storage model

Initial run storage may be ephemeral.

The deployment must state this clearly.

Long-term persistence is not required for the Build Week vertical slice.

### 22.4 Deployment rollback

Rollback should require:

- restoring the previous application version,
- restarting the stateless server,
- retaining no mandatory database migration,
- preserving downloadable bundles independently where required.

---

## 23. Testing Strategy

### 23.1 Test categories

The project should maintain:

- unit tests,
- contract tests,
- verifier regression tests,
- tamper tests,
- CLI integration tests,
- HTTP safety tests,
- fixture end-to-end tests,
- mocked provider tests,
- compatibility tests.

### 23.2 Critical test scenarios

Tests should cover:

- valid manifest,
- unknown manifest fields,
- unsafe paths,
- duplicate artifact paths,
- invalid limits,
- deterministic fixture output,
- malformed provider response,
- mocked OpenAI structured output,
- absent API key behavior,
- no-secret persistence,
- artifact count and byte limits,
- every acceptance-check type,
- v0.1 Proof Bundle compatibility,
- current Proof Bundle verification,
- artifact tampering,
- event tampering,
- metadata tampering,
- original-run preservation,
- Mission Control health,
- path-safe artifact retrieval,
- CSRF protections,
- Host validation,
- CLI exit codes.

### 23.3 Live test policy

Tests must not require a live API call by default.

The OpenAI provider remains:

```text
IMPLEMENTED BUT NOT LIVE-VALIDATED
```

until a controlled real request succeeds.

### 23.4 Supported versions

Build Week compatibility targets:

```text
Python 3.11
Python 3.12
```

---

## 24. Observability and Evidence

### 24.1 Evidence over opaque logs

Operational logs may assist debugging, but verification-relevant facts must be represented in structured evidence.

### 24.2 Safe observability

Operational telemetry must avoid:

- secrets,
- raw authentication values,
- hidden reasoning,
- unnecessary user content,
- uncontrolled environment dumps.

### 24.3 Correlation

A mission should be traceable using:

- mission ID,
- run ID,
- bundle hash,
- event indices,
- provider response identifier where safely available.

---

## 25. Failure Model

The system should clearly differentiate failure domains.

### 25.1 Manifest failure

The requested mission violates schema or policy.

### 25.2 Provider failure

The provider is unavailable, unauthorized, times out, or returns invalid structured output.

### 25.3 Policy failure

The proposal violates artifact limits or path restrictions.

### 25.4 Acceptance failure

The runtime completed safely, but one or more objective requirements did not pass.

### 25.5 Verification failure

Evidence is missing, inconsistent, corrupted, unsupported, or modified.

### 25.6 Operational failure

The server, filesystem, backend, or runtime environment cannot complete the requested operation.

These failures must not be collapsed into one generic error.

---

## 26. Product Metrics

Initial useful measures include:

- percentage of fixture missions producing valid bundles,
- verification success rate for untampered runs,
- detection rate for supported tamper cases,
- median fixture mission duration,
- median independent verification duration,
- manifest rejection accuracy,
- provider parsing failure rate,
- number of secrets detected in persisted evidence: target zero,
- backward-compatibility test success,
- judge time-to-first-verified-run.

The Build Week success metric is not user growth.

It is:

> Can a judge understand, execute, verify, tamper, and re-verify the complete product flow within minutes?

---

## 27. Build Week Judge Path

The preferred evaluation path is:

1. Open Mission Control.
2. Read the trust-boundary notice.
3. Select the checked-in fixture mission.
4. Run the mission.
5. Inspect generated artifacts.
6. Inspect deterministic acceptance checks.
7. Review the event timeline.
8. Observe bundle hash and Merkle root.
9. Run independent verification.
10. Confirm `LOCAL_VERIFIED` and `UNANCHORED`.
11. Open Tamper Lab.
12. Modify a disposable artifact copy.
13. Observe `FAILED` with a precise reason.
14. Repeat with event or metadata tampering.
15. Download or inspect the Proof Bundle.
16. Optionally follow the live GPT-5.6 path when configured.

The complete path should take fewer than five minutes.

The video demonstration should show the central sequence in approximately 90 seconds.

---

## 28. Product Differentiation

Agent Proof Runtime is not primarily:

- an agent framework,
- an LLM wrapper,
- a chat interface,
- a workflow builder,
- a generic observability dashboard,
- a blockchain product,
- a code-execution platform.

It is an execution-evidence layer.

Its differentiation comes from combining:

- predeclared mission contracts,
- constrained provider output,
- deterministic acceptance,
- cryptographic execution receipts,
- independent verification,
- visible tamper detection,
- conservative trust claims.

---

## 29. Roadmap

### Phase 0 — Existing proof slice

- disposable workspace,
- deterministic demo worker,
- artifact capture,
- acceptance result,
- event chain,
- RFC 6962-style Merkle root,
- portable Proof Bundle,
- independent verifier,
- tamper tests,
- static report.

### Phase 1 — Build Week Mission Control

- declarative missions,
- deterministic fixture provider,
- optional OpenAI GPT-5.6 provider,
- structured artifact proposals,
- artifact policy enforcement,
- deterministic acceptance checks,
- extended Proof Bundle,
- Mission Control,
- Tamper Lab,
- competition deployment.

### Phase 2 — Stronger execution boundary

- validated gVisor profile,
- read-only base image,
- controlled mounts,
- enforced egress policy,
- unprivileged execution,
- sandbox escape regression suite.

### Phase 3 — Trust outside the runtime host

- signed receipts,
- external append-only anchor,
- transparency log,
- inclusion proofs,
- key rotation,
- revocation,
- independent timestamping.

### Phase 4 — Interoperability

- standardized schemas,
- in-toto-compatible statements,
- software supply-chain evidence adapters,
- multi-runtime verifier profiles,
- portable policy packs.

### Phase 5 — Regulated execution profiles

- configurable retention,
- PII handling profiles,
- hardware-backed keys,
- remote attestation,
- formal control mapping,
- independent audits.

No roadmap item becomes a product claim before implementation and validation.

---

## 30. Product Invariants

The following rules must remain true as the project evolves:

1. The verifier does not trust a stored runtime success label.
2. The model never determines cryptographic validity.
3. Provider output remains constrained by runtime policy.
4. Evidence survives outside Mission Control.
5. API keys and hidden reasoning never enter the Proof Bundle.
6. Local verification is never mislabeled as external anchoring.
7. Unsupported isolation is never claimed as active.
8. Tamper demonstrations never modify the original run.
9. New bundle versions do not silently invalidate older supported receipts.
10. Human approval remains separate from technical verification.

A change violating one of these invariants requires an explicit architecture decision.

---

## 31. Definition of Done — Build Week v0.2

The Build Week product is complete when:

- the legacy test suite remains green,
- a versioned safe mission can be loaded,
- the fixture provider completes the mission without secrets,
- the same provider contract supports the OpenAI implementation,
- proposed artifacts are safely materialized,
- deterministic acceptance evidence is recorded,
- a versioned Proof Bundle is produced,
- the independent verifier returns `LOCAL_VERIFIED`,
- a modified artifact causes verification to return `FAILED`,
- a modified event causes verification to return `FAILED`,
- modified critical metadata causes verification to return `FAILED`,
- the original run remains unchanged,
- Mission Control exposes the complete judge path,
- `/health` succeeds,
- documentation distinguishes baseline from Build Week work,
- no secret or generated run data is tracked,
- the final branch and Codex session evidence are preserved,
- deployment limitations are stated honestly.

---

## 32. Final Product Statement

Agent Proof Runtime does not ask users to believe that an autonomous system behaved correctly.

It gives them a contract, an execution receipt, and an independent method of checking the evidence.

The product begins with a local, conservative verification boundary.

Its long-term direction is an interoperable trust layer for autonomous execution.

The central promise remains unchanged:

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.
