# Part VIII — The Path Forward

## Chapter 29 — Roadmap

APR's roadmap strengthens two different axes over time: execution isolation and
trust outside the runtime host. Neither should be confused with adding more model
features.

### Phase 0 — Local proof slice

The original vertical slice established the evidence core:

- disposable workspace;
- deterministic demo worker;
- artifact capture and acceptance result;
- SHA-256 event chain;
- RFC 6962-style Merkle root;
- portable Proof Bundle v0.1;
- independent verifier;
- tamper regression tests;
- static HTML report.

This phase proved that an execution receipt could be produced and independently
recomputed without a web interface or external service.

### Phase 1 — Build Week Mission Control

The current active phase extends that core with:

- Mission Manifest v1;
- deterministic fixture provider;
- optional OpenAI GPT-5.6 provider;
- structured artifact proposals;
- exact artifact policy;
- six deterministic acceptance check types;
- Proof Bundle v1;
- version-aware independent verification;
- Mission Control;
- disposable artifact, event, and metadata Tamper Lab;
- Docker packaging and hosted deployment path.

The repository records the fixture path, local/container judge flow, hosted Mission
Control, and one controlled live provider run as validated within their stated
boundaries.

### Phase 2 — Stronger execution boundary

The next isolation phase requires real runtime validation, not only adapter code:

- a Linux Docker host with registered `runsc`;
- pinned and reproducible workload images;
- read-only base filesystem and controlled mounts;
- enforced egress policy;
- unprivileged execution;
- timeout, fork, resource-exhaustion, and escape regression tests;
- comparison of gVisor with a microVM backend where cost and startup latency justify it.

Success in this phase would justify a stronger execution security label. It would
not automatically change `UNANCHORED`.

### Phase 3 — Trust outside the runtime host

External trust requires another authority or preserved system boundary:

- signed receipts;
- append-only anchor service on a separate host;
- transparency log;
- inclusion proofs;
- independent timestamps;
- key rotation and revocation;
- key custody outside the runtime process.

Only this phase can support statuses such as `SIGNED_ONLY` or `ANCHORED`, and only
after their exact semantics and validation are defined. A root submitted somewhere
is not enough; clients must verify signatures, log identity, inclusion, and freshness.

### Phase 4 — Interoperability

Once evidence semantics are stable, APR can map them into broader ecosystems:

- published schema and canonicalization profiles;
- cross-language test vectors;
- independently implemented verifiers;
- in-toto-compatible statements and predicates;
- software supply-chain evidence adapters;
- portable policy packs;
- multiple runtime profiles sharing receipt semantics.

Interoperability is valuable because no single agent runtime should own the only
verifier of its receipts.

### Phase 5 — Regulated execution profiles

Regulated environments may require:

- configurable evidence retention;
- explicit PII classification and handling;
- HMAC tokenization or privacy-preserving identifiers;
- hardware-backed signing keys;
- remote attestation;
- formal control mapping;
- role-based access and separation of duties;
- independent cryptographic and threat-model audits.

These requirements are not a natural consequence of adding a dashboard. They are a
different assurance level and must be designed, implemented, tested, operated, and
audited as such.

### Roadmap discipline

Every phase follows the same rule: code, tests, and observed validation must precede
stronger product claims. The roadmap is a direction, not borrowed credibility.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 29
- `docs/ROADMAP.md`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 30 — Product Invariants

Features can evolve while the product's core meaning remains stable. APR defines ten
invariants that any future architecture must preserve unless an explicit,
reviewable decision changes them.

### 1. The verifier does not trust stored runtime success

The runtime may record a claim, but verification must derive its own result from the
supported evidence. A UI badge or bundle field cannot become the proof authority.

### 2. The model never determines cryptographic validity

A provider may create content, summarize, or explain. It may not decide whether
hashes, chains, roots, signatures, or inclusion proofs are valid.

### 3. Provider output remains constrained by runtime policy

Structured output improves reliability but does not grant authority. Paths, media
types, counts, sizes, execution permissions, and side effects remain under explicit
runtime enforcement.

### 4. Evidence survives outside Mission Control

The portable receipt and verifier are primary. A user interface may disappear,
change, or be replaced without making historical evidence meaningless.

### 5. Secrets and hidden reasoning never enter the Proof Bundle

Credentials, authorization headers, secret environment variables, raw
chain-of-thought, and uncontrolled internal traces are outside the evidence contract.
The absence of those values must be tested.

### 6. Local verification is never mislabeled as external anchoring

`LOCAL_VERIFIED` and `UNANCHORED` answer different questions. A local bundle hash,
Merkle root, hosted URL, or successful API call does not create non-repudiation.

### 7. Unsupported isolation is never claimed as active

An implementation path, Dockerfile, or simulated test is not a real gVisor or
microVM validation. Backends must fail closed and report actual detection state.

### 8. Tamper demonstrations never modify the original run

Security demonstration uses a disposable copy and verifies original fingerprints
before and after. Evidence evaluation must not destroy its source.

### 9. New bundle versions do not silently invalidate old receipts

Verification dispatches by schema version. New semantics require a new version,
clear rejection of unsupported formats, compatibility tests, and migration guidance
where appropriate.

### 10. Human approval remains separate from technical verification

Integrity evidence informs a decision. It does not determine strategic value,
ethics, legal sufficiency, customer acceptance, or deployment authority.

### Invariants as a review tool

These rules turn architectural review into concrete questions. Does a new provider
receive arbitrary command execution? Does a hosted redesign hide `UNANCHORED`? Does
a bundle extension persist raw model traces? Does a performance optimization stop
reproducing acceptance? Does a new UI invent a success state? Does a migration drop
v0.1 verification?

If the answer threatens an invariant, the change needs an explicit architecture
decision and evidence. Speed is not a reason to make the trust model implicit.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 30
- `docs/PROJECT_MANIFESTO.md` section 13

## Chapter 31 — Definition of Done: Build Week v0.2

A vertical slice is done when the complete operator story works and its negative
claims remain honest. APR's Definition of Done combines compatibility, functionality,
security regression, documentation, and validation.

### Contract and provider

- A versioned safe mission loads under strict validation.
- Fixture mode completes without a secret or network call.
- The optional OpenAI provider implements the same proposal boundary.
- Structured output cannot grant arbitrary host commands or paths.
- Provider absence and missing credentials fail clearly.

### Runtime and acceptance

- Proposed artifacts are materialized only after exact policy enforcement.
- Required files, media types, duplicate paths, counts, and byte limits are enforced.
- Deterministic acceptance evidence is recorded.
- Mission failure remains distinct from proof failure.

### Receipt and verification

- A versioned Proof Bundle is produced.
- The independent verifier returns `LOCAL_VERIFIED` for untouched valid evidence.
- Artifact modification returns `FAILED`.
- Event modification returns `FAILED`.
- Critical metadata modification returns `FAILED`.
- The original run remains unchanged after every Tamper Lab case.
- v0.1 and v0.2 receipts retain their verification semantics.

### Operator surfaces

- The CLI exposes validation, execution, verification, tampering, diagnostics, and
  Mission Control startup.
- Mission Control exposes the complete judge path.
- The interface maps statuses to evidence and shows trust boundaries.
- `/health` succeeds.
- HTTP controls cover Host validation, CSRF, CSP, paths, traversal, and symlinks.

### Repository and operations

- The legacy suite remains green on supported Python versions.
- CI executes the fixture path without a live API call.
- Generated runs and secrets are not tracked.
- Baseline, collaboration, architecture, deployment, and validation records exist.
- The Build Week branch preserves implementation lineage.
- Deployment limitations are stated honestly.

### Recorded completion state

The repository's gap audit marks the competition-critical fixture vertical slice as
complete and independently verifiable. It records the OpenAI provider as delivered
and live-validated in one controlled local run. It records the Docker image and
public Mission Control judge flow as validated. It also leaves two major boundaries
open by design:

- real Linux Docker + `runsc` validation for hardened gVisor execution;
- external signing or append-only anchoring for non-repudiation.

Those open items do not make the delivered vertical slice incomplete. They prevent
the current product from claiming a stronger assurance level.

Definition of Done is therefore not "everything on the roadmap exists." It is "the
locked slice works end to end, failures are observable, tests protect the contract,
and every limitation is labeled accurately."

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 31
- `docs/BUILD_WEEK_GAP_AUDIT.md`
- `docs/LIVE_VALIDATION.md`
- `docs/HOSTED_VALIDATION.md`

## Chapter 32 — Final Product Statement

Autonomous systems will increasingly act before a human reviews every individual
step. That transition cannot rest on screenshots, confidence scores, and
self-reported success.

An agent can say that it completed a task. It can produce a polished artifact. It
can narrate a plausible execution. None of those things independently establishes
what contract governed the run, what authority the provider held, which bytes were
materialized, which objective checks actually passed, or whether the evidence
changed afterward.

Agent Proof Runtime begins by making the contract explicit.

The Mission Manifest states what should happen, what the provider may produce, how
large the output may become, and which objective conditions will be evaluated. The
provider proposes structured artifacts but cannot expand its own authority. The
runtime enforces paths, media types, counts, and byte limits before creating files.
The acceptance engine evaluates bounded deterministic predicates without asking the
model to grade itself.

The runtime then leaves a receipt. Events are canonicalized, hashed, and linked.
Artifact bytes receive digests. Event hashes form a domain-separated Merkle tree.
The mission, provider metadata, artifacts, acceptance evidence, events, and trust
labels become a versioned Proof Bundle with a recomputable whole-document hash.

Another process opens that receipt and starts again. It does not accept the stored
success label. It resolves paths safely, reads the artifacts, rebuilds hashes and
links, reproduces acceptance, and derives its own result. Mission Control explains
the evidence, but it is not the evidence. Tamper Lab changes a disposable copy so
the user can watch verification fail while the original remains intact.

The result is not omniscience.

APR does not prove that an agent chose the best strategy. It does not turn a passed
file check into semantic truth. It does not call a local hash an external signature.
It does not call an ordinary process a secure sandbox. It does not replace the human
who must decide whether an output is useful, ethical, legal, or ready to deploy.

Those limits are part of the product, not footnotes to hide.

The current system proves a narrower and more practical proposition: autonomous
work can be placed under an explicit contract, constrained to a declared artifact
surface, recorded as structured evidence, and checked independently for local
integrity. That foundation can later gain stronger isolation, external signatures,
append-only anchoring, interoperability, and regulated profiles without abandoning
the semantics of the original receipt.

The product doctrine fits into four lines:

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.

Agent Proof Runtime does not ask users to trust autonomous execution because a model
sounds certain.

It gives them a contract, a receipt, and an independent method of checking the
evidence.

That is the beginning of accountable autonomy.

That is proof before trust.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md` section 16
- `docs/PRODUCT_BLUEPRINT.md` section 32
