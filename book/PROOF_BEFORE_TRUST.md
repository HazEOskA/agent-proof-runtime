---
author: Bartosz Osiński (Osa)
date: July 2026
description: "A practical and evidence-bounded account of Agent Proof
  Runtime: mission contracts, controlled artifacts, deterministic
  acceptance, cryptographic execution receipts, independent
  verification, and honest trust boundaries."
lang: en-US
subtitle: Engineering Verifiable Execution for Autonomous AI Agents
title: Proof Before Trust
---

# Proof Before Trust

## Engineering Verifiable Execution for Autonomous AI Agents

**Bartosz Osiński (Osa)**  
**Agent Proof Runtime**  
**First edition — July 2026**

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.

# Preface

## Why this book exists

Autonomous AI systems are crossing a line. They no longer only answer
questions. They create files, modify repositories, call tools, run
workflows, and prepare actions that may affect customers,
infrastructure, money, or public systems. The industry has become very
good at making these systems look capable. It is much less mature at
showing what actually happened after an autonomous task ends.

Most agent products present one of three things: a polished final
answer, an activity feed, or a confidence score. All three can be
useful. None is independent proof. A final answer can omit failed steps.
An activity feed can be incomplete or changed. A confidence score is
still a claim made by the system being evaluated.

Agent Proof Runtime began with a deliberately narrower question:

> Can an agent mission leave behind a portable execution receipt that
> another process can verify without trusting the agent, the runtime’s
> stored success label, or the user interface?

That question leads to a different product architecture. The mission
must be declared before execution. Model output must be treated as
untrusted data. The runtime must enforce explicit authority over paths,
file types, counts, and sizes. Objective acceptance conditions should be
deterministic. Important events and artifacts should be bound to
cryptographic digests. A separate verifier should derive its own result.
The final operator should see both the evidence and the limits of that
evidence.

This book explains that architecture as a product and as an engineering
method. It is not a theoretical security proof and not a claim that APR
solves every problem in agent safety. It describes the system that
exists in the repository, the boundaries the project states openly, and
the path from a local proof slice toward stronger external trust.

## A book built from a repository

The factual hierarchy for this manuscript is explicit:

1.  implementation and tests,
2.  locked architecture documents,
3.  validation records,
4.  product doctrine and roadmap,
5.  this narrative explanation.

If prose and implementation disagree, the implementation and its
reproducible tests win. If two documents describe different moments in
time, the later validation record governs the current claim while the
older document remains useful provenance. The manuscript therefore
separates four kinds of statement:

- **Implemented:** code exists in the active product branch.
- **Tested:** an automated or controlled validation covers the behavior.
- **Observed:** a dated validation record reports a real run or
  deployment.
- **Roadmap:** the capability is intended but must not be presented as
  delivered.

This matters because systems about trust lose credibility the moment
their own claims outrun their evidence.

## The central distinction

APR does not try to prove that an AI made the best decision. That claim
is too broad for the evidence the runtime can currently produce. APR
makes narrower claims that can be checked:

- a particular mission contract was recorded;
- a provider returned a structured proposal;
- only declared artifacts were materialized;
- deterministic checks produced recorded results;
- files still match their recorded hashes;
- events form the expected hash chain;
- the Merkle root and whole-bundle hash can be recomputed;
- protected changes become detectable within the local trust boundary.

Those claims are useful precisely because they are limited.
`LOCAL_VERIFIED` means internal evidence is consistent. It does not mean
the run is externally signed, remotely anchored, semantically perfect,
or safe against a fully privileged host administrator who replaces the
evidence and recomputes it. APR uses `UNANCHORED` and `development-only`
to keep those limits visible.

## The operating doctrine

The complete product can be summarized in four sentences:

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.

Each sentence assigns authority to a different component. The provider
is allowed to propose artifacts, not to authorize itself. The runtime is
allowed to enforce policy and build evidence, not to be the sole judge
of that evidence. The verifier is allowed to calculate integrity, not to
decide whether a business outcome is desirable. The human remains
responsible for approval, deployment, and consequence.

That separation is the recurring pattern throughout the next thirty-two
chapters.

## How to use this book

Readers building agent infrastructure can treat the book as an
architectural walkthrough. Security reviewers can focus on Parts II, IV,
V, and VI. Product operators can begin with Parts I, VII, and VIII. A
judge or evaluator can follow the five-minute path in Chapter 27 and
then return to the underlying contracts.

The examples intentionally favor a deterministic fixture. A useful
verification product cannot require a third-party model, a network call,
or a secret merely to demonstrate its core correctness. APR’s optional
OpenAI provider traverses the same proposal, policy, acceptance, event,
bundle, and verification contracts, but it is not the root of trust.

The project begins with proof before trust. The book begins at the same
place: not with a promise that autonomous agents are reliable, but with
a method for making their execution claims inspectable.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md`
- `docs/PRODUCT_BLUEPRINT.md`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md`
- `docs/LIVE_VALIDATION.md`
- `docs/HOSTED_VALIDATION.md`

# Part I — The Trust Gap and the Product

## Chapter 1 — Executive Summary

An autonomous agent can create a convincing result while leaving the
operator unable to answer basic questions about the execution. Which
mission did it really follow? Which provider response influenced the
output? Which files were permitted? Which checks ran? Did the evidence
change after completion? Can anybody other than the system that
performed the work verify its claims?

Agent Proof Runtime is an execution-evidence layer designed around those
questions. Its purpose is not to make an agent intelligent and not to
replace an agent framework. APR sits around an autonomous task and turns
a declared mission into a portable receipt of execution.

The Build Week path is intentionally narrow:

``` text
Mission Manifest
  -> strict validation
  -> fixture or OpenAI provider
  -> structured artifact proposal
  -> runtime policy enforcement
  -> controlled text materialization
  -> deterministic acceptance checks
  -> event hash chain + Merkle root
  -> Proof Bundle
  -> independent verification
  -> Mission Control + Tamper Lab
```

The flow begins with a contract rather than a prompt. A versioned
Mission Manifest declares the goal, provider, model, exact artifact
surface, resource limits, acceptance checks, and reasoning-retention
policy. Unknown fields, duplicate JSON keys, absolute paths, traversal
segments, unsupported media types, malformed checks, and invalid limits
are rejected before execution.

The selected provider has a deliberately small job: return a structured
artifact proposal. In deterministic mode, a fixture produces repeatable
output without a network or secret. In optional live mode, the OpenAI
adapter requests strict Structured Output from GPT-5.6. Both return the
same conceptual object. Neither is granted authority to run shell
commands, choose arbitrary filesystem paths, or declare its own proof
valid.

The runtime then applies policy that exists outside the model. It checks
exact path membership, media types, required files, duplicate paths,
per-file and total byte limits, and file-count limits. It creates a
fresh destination and writes permitted text artifacts with exclusive
creation semantics. The system re-reads the files, calculates digests,
and evaluates six allowlisted deterministic check types: `file_exists`,
`file_count`, `contains_text`, `json_valid`, `json_required_keys`, and
`maximum_size`.

During execution, significant transitions become canonical events. Each
event is bound to the previous event through SHA-256. Event hashes
become leaves in an RFC 6962-style Merkle construction. The final Proof
Bundle contains the canonical mission, provider metadata safe for
persistence, artifact records, acceptance evidence, events, integrity
roots, runtime claim, and anchor status.

The important step comes afterward. A separate verifier opens the bundle
and does not trust the stored success label. It validates the schema,
resolves artifact paths safely, rejects symlinks and traversal,
re-hashes files, rebuilds the event chain, recomputes the Merkle root
and whole-bundle hash, reproduces acceptance checks, and cross-checks
critical metadata. Its result is derived from evidence.

This produces a small but meaningful trust vocabulary:

| Label              | Meaning                                                                                                                   |
|--------------------|---------------------------------------------------------------------------------------------------------------------------|
| `LOCAL_VERIFIED`   | The independent verifier found the bundle and referenced artifacts internally consistent within the local trust boundary. |
| `FAILED`           | At least one required schema, path, artifact, event, acceptance, or integrity condition did not hold.                     |
| `UNANCHORED`       | No independent external log, signature service, or hardware-backed authority vouched for the bundle.                      |
| `development-only` | The controlled-artifact/local process path is not presented as hostile-code isolation.                                    |

These labels prevent a common category error. Mission success and proof
validity are not the same thing. A mission may legitimately fail its
acceptance criteria while the proof remains `LOCAL_VERIFIED`, because
the verifier confirms that the failure was recorded consistently.
Conversely, an artifact may look useful while its proof is `FAILED`,
because the evidence was altered or became inconsistent.

Mission Control makes this flow visible. It allows an operator to select
a checked- in mission, run it through the fixture or configured live
provider, inspect artifacts, view checks and events, see the Merkle root
and bundle hash, and request independent re-verification. The interface
is an adapter over the same runner and verifier used by the CLI; it is
not an alternative source of truth.

Tamper Lab completes the demonstration. It copies a verified run,
changes one artifact, event, or critical metadata field, runs the
verifier against the copy, reports the exact failure, deletes the
disposable copy, and confirms the original run’s fingerprint remains
unchanged. The product does not merely say that tampering is detectable.
It lets the user observe detection.

The current result is useful but deliberately bounded. The fixture path,
verifier, Mission Control, Tamper Lab, Docker deployment, hosted judge
flow, and one controlled GPT-5.6 provider run have validation records in
the repository. External anchoring, out-of-host signing, hostile-code
isolation in the controlled-artifact path, multi-tenant authentication,
HSM/TEE guarantees, and real gVisor execution remain outside the
delivered trust boundary.

APR therefore makes a precise promise: it converts autonomous agent
activity into independently verifiable execution evidence. It does not
ask the evidence to prove more than it can.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` sections 1 and 5
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 2 — Product Definition

Agent Proof Runtime is best understood by separating it from adjacent
product categories. It is not primarily a chat interface, an agent
framework, a model router, a generic observability dashboard, a
blockchain product, or a full code- execution cloud. Those products may
become sources or consumers of APR evidence, but none defines its
central role.

The one-sentence definition is:

> Agent Proof Runtime converts autonomous agent activity into
> independently verifiable execution evidence.

Three words in that sentence carry most of the architecture.

**Execution** means APR cares about the path between intention and
output, not only the final content. A useful artifact without a declared
mission, event record, or acceptance evidence may still be useful, but
it is not a complete APR result.

**Evidence** means the product records inspectable facts: normalized
contracts, provider metadata, artifact bytes and hashes, deterministic
observations, ordered events, and integrity roots. Evidence is different
from an explanation. An agent may explain what it believes happened. APR
records material that can be checked.

**Independently verifiable** means the process that produced the
evidence is not the only authority deciding whether that evidence is
internally consistent. The verifier may share canonicalization and
deterministic evaluation functions because identical rules must be
reproducible, but it does not trust the runtime’s final status. It
derives a verdict from the bundle and files it reads.

The product promise can then be expressed as a concrete handoff. A user
submits a versioned mission and receives:

- materialized artifacts;
- a structured event timeline;
- deterministic acceptance results;
- cryptographic integrity metadata;
- a portable Proof Bundle;
- an independently derived verification result.

This is narrower than promising that the agent was correct. APR does not
determine whether a design is beautiful, a business decision is wise, a
legal analysis is complete, or generated code is free of every
vulnerability. It can prove that a declared file existed, contained
required text, formed valid JSON, included required keys, remained below
a size limit, and still matches its recorded digest. It can prove that
the evidence structure recomputes. It cannot turn those objective facts
into universal semantic truth.

The primary user journey reflects this restraint:

1.  Select a safe, declared mission.
2.  Run it with a deterministic fixture or configured live provider.
3.  Inspect the generated artifacts.
4.  Review objective acceptance checks.
5.  Examine the event timeline and integrity values.
6.  Invoke independent verification.
7.  Create a disposable tampered copy.
8.  Observe verification fail for a precise reason.

That final contrast matters. Trust mechanisms often remain abstract
until failure is visible. The difference between the untouched
`LOCAL_VERIFIED` run and a modified `FAILED` copy gives operators a
working mental model of what APR protects.

The product also creates a useful interface boundary for agent builders.
Providers do not need to understand hash chains or the bundle schema.
They need to return a valid proposal. Agent frameworks do not need to
become cryptographic verifiers. They can submit bounded work and consume
a receipt. Mission Control does not need to reimplement integrity logic.
It calls the same verifier. Each component has a smaller responsibility
than a monolithic “trusted agent” would require.

APR is therefore both a product and an architectural position.
Autonomous systems should not earn trust by narrating their own success.
They should operate under an explicit contract, leave portable evidence,
and accept an independent check.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md` sections 3–5
- `docs/PRODUCT_BLUEPRINT.md` sections 2 and 4

## Chapter 3 — Target Users

The first APR users are not people looking for another general-purpose
chatbot. They are builders and reviewers who already understand that
autonomous execution creates an operational gap.

### Developers of autonomous agents

Agent developers need to debug more than a final response. They need to
know which contract reached the runtime, what structured output arrived,
what policy rejected, which files were accepted, and which deterministic
conditions held. A Proof Bundle turns those facts into a stable artifact
that survives beyond terminal output.

For a coding agent, this could mean declaring an exact patch artifact,
expected file count, byte ceiling, and machine-checkable properties
before the model is invoked. APR does not yet claim safe arbitrary code
execution in the Build Week path, but the contract-and-receipt pattern
applies directly to stronger future backends.

### Agentic workflow engineers

Workflow builders often connect probabilistic decisions to deterministic
tools. Their systems may succeed for weeks and then fail in a way that
is difficult to reconstruct. APR offers a neutral boundary between a
provider’s proposal and the side effects permitted by a runtime. The
workflow can carry a bundle hash and run identifier into later stages
instead of relying on a mutable activity log.

### AI infrastructure and QA teams

Infrastructure teams care about reproducibility, versioning, and
compatibility. APR’s fixture-first path is valuable because it separates
runtime correctness from provider availability. The same mission can
traverse proposal parsing, policy, materialization, acceptance, event
creation, bundle generation, and verification in CI without a key or
external request.

AI QA teams can use the failure vocabulary to distinguish categories
that generic test dashboards often collapse: invalid manifest, provider
failure, policy failure, acceptance failure, verification failure, and
operational failure. A precise failure domain is the beginning of useful
remediation.

### Security-conscious automation teams

Security reviewers are natural users because APR makes its trust
boundary explicit. They can inspect which fields are canonicalized, how
paths are resolved, whether symlinks are rejected, how event linkage
works, and what the verifier recomputes. They can also see what remains
unsolved. A local unsigned bundle is not presented as non-repudiation. A
Docker image is not automatically called a hostile-code sandbox.

### Technical auditors and judges

An auditor should not need to understand every source file before
evaluating a small claim. APR provides a short path from mission to
artifact to receipt to verification to deliberate failure. The Proof
Bundle remains available for deeper inspection, while Mission Control
makes the evidence legible.

### Future regulated operators

Financial, healthcare, public-sector, and compliance teams are plausible
later users, but their presence on the roadmap must not inflate current
claims. They may require signed receipts, trusted timestamps, external
append-only logs, durable retention, identity, role-based access, PII
controls, hardware-backed keys, and independent audits. The local Build
Week profile is a foundation, not a regulatory certificate.

The common trait across these groups is not industry. It is the need to
separate an autonomous system’s assertion from independently checkable
evidence.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 3
- `docs/ROADMAP.md`

## Chapter 4 — User Roles

Reliable agent systems become easier to reason about when responsibility
is divided by role. APR defines six conceptual roles. A small
installation may place several roles in one person or process, but their
authority should still remain distinct.

### The Mission Author

The Mission Author decides what the task means before execution. This
role defines the goal, provider policy, model request, exact artifact
contract, limits, deterministic acceptance checks, and
analysis-retention policy.

The author is powerful because an incorrect contract can make a run
useless while remaining perfectly verifiable. If the manifest checks
only that `report.json` exists, APR can prove existence but not whether
the report contains the business analysis the operator needed. Good
verification begins with a good contract.

The author cannot control the verifier’s result. Changing the manifest
after a run changes its canonical hash and should invalidate the
relationship to the recorded evidence.

### The Operator

The Operator starts missions, inspects artifacts, reviews checks,
invokes verification, and decides what to do with the result. The
operator may accept, reject, revise, or stop a downstream action. APR
provides evidence; it does not seize this authority.

This distinction is crucial in real workflows. `LOCAL_VERIFIED` is not
an automatic deployment approval. It says that the available evidence is
internally consistent. The operator may still reject the artifact for
quality, ethics, strategy, or risk.

### The Provider

The Provider proposes structured artifacts. It may be the deterministic
fixture, GPT-5.6 through the optional OpenAI adapter, or a future
compatible integration. The provider is not allowed to write arbitrary
host files, choose shell commands, expand the manifest, waive byte
limits, or declare cryptographic validity.

Treating the provider as untrusted input is not an insult to the model.
It is a sound systems boundary. Powerful components should receive only
the authority required for their task.

### The Runtime

The Runtime validates the mission, invokes the selected provider, parses
the proposal, enforces policy, materializes permitted artifacts, runs
deterministic checks, records events, and builds the Proof Bundle. It is
the execution coordinator and evidence producer.

The runtime does write a claimed status into the bundle because
operational state must be recorded. That claim is evidence input, not
the final verdict.

### The Independent Verifier

The verifier reads the bundle and artifacts after execution. It
validates supported schema versions, checks paths, re-hashes files,
rebuilds chains and roots, reproduces acceptance evidence, cross-checks
metadata, and emits its own result. It does not ask the provider whether
the run was valid and does not trust Mission Control’s badge.

Independence here is logical and procedural, not yet external-host
independence. The verifier can run as a separate command and on copied
evidence, but a privileged attacker who owns the host may still replace
both evidence and verifier. External trust is a later phase.

### The Judge or Auditor

The Judge or Auditor evaluates the product through a controlled path.
This role starts with a checked-in fixture mission, observes a verified
result, changes a disposable copy in Tamper Lab, and confirms that
failure is detected while the original remains intact. The role is
deliberately given a reproducible path rather than a promotional demo
that depends on hidden setup.

Together, these roles define APR’s authority model:

| Role           | May do              | Must not be treated as         |
|----------------|---------------------|--------------------------------|
| Mission Author | Declare contract    | Proof authority                |
| Operator       | Decide and approve  | Cryptographic calculator       |
| Provider       | Propose artifacts   | Host administrator or verifier |
| Runtime        | Enforce and record  | Sole judge of its own evidence |
| Verifier       | Recompute integrity | Business approver              |
| Judge/Auditor  | Evaluate claims     | Hidden privileged operator     |

The separation prevents one component from becoming author, executor,
witness, judge, and approver at the same time.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 4
- `docs/PROJECT_MANIFESTO.md` sections 5, 6, and 12

# Part II — Goals, Boundaries, and Contracts

## Chapter 5 — Product Goals

Agent Proof Runtime has a long-term direction, but its current value
comes from a complete vertical slice. A small system that actually runs,
records, verifies, and fails visibly is more useful than a broad trust
architecture made mostly of future claims.

The Build Week goal can be drawn as one continuous chain:

``` text
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

Each arrow matters. Removing the manifest turns the run into an
unbounded prompt. Removing policy gives provider output direct
authority. Removing deterministic checks leaves only subjective
evaluation. Removing the chain or artifact hashes makes later
modification harder to detect. Removing the independent verifier leaves
the executor judging itself. Removing the Tamper Lab makes the integrity
claim less understandable to a user.

### Functional goals

The current product must support versioned mission definitions and
remain usable without external secrets. That is why the fixture provider
is a first-class component rather than an emergency fallback. A judge,
developer, or CI runner can exercise the complete evidence path
deterministically.

The optional live provider must share the same boundary. It may change
the content proposal, response identifier, token usage, and latency, but
it must not create a second policy model or a weaker verification path.
Fixture and live execution meet at the `ArtifactProposal` and safe
provider metadata contracts.

The system must constrain artifacts, execute only allowlisted objective
checks, preserve older bundle verification, provide both CLI and Mission
Control access, and make evidence portable outside the interface. These
are product goals because they shape the user experience, not only
internal engineering.

### Trust goals

APR must distinguish at least four independent questions:

1.  Did execution complete operationally?
2.  Did the declared acceptance checks pass?
3.  Is the recorded evidence internally consistent?
4.  Has an external authority anchored or signed that evidence?

One green status cannot answer all four. A provider can complete while
acceptance fails. Acceptance can fail while the proof remains valid. A
proof can be locally valid while externally unanchored. A hosted UI can
be healthy while the execution backend remains development-only.

This separation creates honest composability. A later signing service
can add an external trust result without redefining `LOCAL_VERIFIED`. A
stronger execution backend can improve isolation without changing the
meaning of an artifact digest.

### Usability goals

Verification infrastructure fails as a product if only its authors can
operate it. The repository therefore defines a judge path that should
complete within minutes: run a checked-in mission, inspect evidence,
verify it, tamper with a copy, and see a precise failure. The CLI
provides a transparent automation surface; Mission Control provides
legibility.

The result is not “maximum security in one week.” It is a complete,
defensible execution-evidence loop with clear seams for stronger future
components.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 5
- `docs/BUILD_WEEK.md`

## Chapter 6 — Explicit Non-Goals

Trust products are often damaged by their adjectives. Words such as
secure, verified, tamper-proof, isolated, and compliant can suggest
guarantees far beyond the implemented boundary. APR uses explicit
non-goals to prevent that drift.

The Build Week system does not claim secure execution of arbitrary
hostile code. Its controlled-artifact path writes allowlisted text
artifacts and never turns provider output into shell commands. The older
local-process harness is useful for development but is not a kernel
security boundary. A Docker container improves packaging and process
separation, but Docker alone is not proof against hostile workloads.

The repository contains a fail-closed Docker + gVisor adapter.
Fail-closed means that when Docker does not report the `runsc` runtime,
APR reports the backend as unavailable rather than silently falling back
to `runc` while claiming gVisor protection. Simulated tests validate the
adapter logic. Real gVisor execution is still unvalidated in the
recorded environment because `runsc` was not installed.

APR also does not provide external non-repudiation. A bundle hash
detects changes only when compared within the declared trust model. If
an attacker has full control of the host, can replace artifacts and
bundle, and can recompute all local hashes, the current system has no
external witness that preserves the original value. That is why every
current receipt is `UNANCHORED`.

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

These exclusions are not a confession that the product lacks purpose.
They are a map of the claim boundary. The delivered system can still
detect accidental or unauthorized modification of protected evidence
within the local model. It can still make provider output safer by
constraining authority. It can still reproduce objective checks. It can
still create a portable record that a future external anchor may sign.

Non-goals also reduce attack surface. The Build Week hosted path does
not execute model-generated shell commands, install packages, or accept
arbitrary host paths. It does not need to solve general remote code
execution because its provider contract is deliberately limited to text
artifact proposals. Scope becomes a security mechanism.

The practical rule is simple:

> Never promote a roadmap component into a present-tense guarantee
> before a real implementation and validation record exists.

This rule applies even when code exists. An adapter may be implemented
but not validated against the real runtime. A provider may be
unit-tested with a fake client but not yet observed in a controlled live
call. A deployment file may exist without a successful public health
check. APR’s documents preserve those temporal distinctions.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 6
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` threat and trust boundary
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 7 — Canonical Product Objects

APR is organized around six canonical objects. Clear objects reduce
ambiguity between intent, proposal, side effect, evidence, and judgment.

### 1. Mission Manifest

The Mission Manifest is a versioned declaration of what should happen
and what is permitted. It contains mission identity, title, goal,
provider and model requests, an artifact contract, bounded limits,
deterministic acceptance checks, and analysis policy. The normalized
manifest is hashed before provider execution.

The manifest is not merely configuration. It is the pre-execution
contract against which later behavior is interpreted.

### 2. Artifact Proposal

The provider returns an `ArtifactProposal`: a structured collection of
proposed text artifacts. Each item includes a relative path, media type,
and content. The proposal is untrusted input. It becomes useful only
after parsing and policy checks.

This object prevents a provider response from being confused with a host
action. The model proposes; the runtime disposes.

### 3. Materialized Artifact

A Materialized Artifact is a file that passed the contract and was
written inside the controlled run directory. Its record includes path,
media type, size, and SHA-256 digest. The bytes on disk—not the
provider’s description—are the object the verifier later re-hashes.

### 4. Event Record

An Event Record captures a significant transition in canonical form. The
event is linked to its predecessor and contains hashes of relevant
inputs, outputs, and details. Events form an ordered execution account
rather than an unstructured log.

### 5. Proof Bundle

The Proof Bundle is the portable receipt. Version `apr.proof-bundle.v1`
carries the canonical mission and its hash, provider metadata, events,
artifacts, acceptance evidence, verification context, integrity roots,
claimed runtime status, and anchor state. Older v0.1 and v0.2 bundles
remain supported by version-aware verification.

The bundle is the product’s primary evidence artifact. Mission Control
visualizes it, but the interface is not required to verify it.

### 6. Verification Result

The Verification Result is the independent verdict produced by replaying
the supported integrity rules. It includes a status and exact reasons
when checks fail. It is not stored success being echoed back to the
user.

### Object relationships

The six objects create a chain of authority:

``` text
Manifest authorizes a bounded proposal surface
Proposal is filtered into materialized artifacts
Events record important transitions
Bundle packages the evidence
Verifier derives a result from bundle + artifacts
Operator decides what the verified evidence means for action
```

This separation avoids a common design error: storing one large “run
result” object that mixes intent, provider output, runtime action,
evidence, and approval. When those concepts are collapsed, it becomes
difficult to say which fields are claims, which are observations, and
which must be recomputed.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 7
- `src/agent_proof_runtime/mission_v1.py`
- `src/agent_proof_runtime/providers.py`
- `src/agent_proof_runtime/validator.py`

## Chapter 8 — Mission Manifest

Every verifiable run begins before the provider is called. The Mission
Manifest freezes the contract that gives later evidence meaning.

APR’s Build Week manifest uses schema version `apr.mission.v1`.
Conceptually, it defines:

``` text
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

The exact implementation is intentionally strict. The parser rejects
unknown top-level and nested fields instead of ignoring them. It rejects
duplicate JSON keys because a document whose meaning changes between
parsers cannot be a stable contract. It rejects duplicate artifact
paths, absolute paths, traversal segments, malformed POSIX-relative
paths, unsupported media types, invalid integer limits, oversized input,
malformed check structures, and fixture content that falls outside the
declared contract.

Strictness serves two purposes. First, it blocks accidental ambiguity. A
misspelled field should fail visibly rather than silently removing a
control. Second, it makes canonical hashing meaningful. Two systems
should not accept subtly different interpretations of the same JSON
text.

### Artifact authority

The manifest defines exact artifact entries and global limits. A
provider cannot create an additional file because it seems helpful. It
cannot change a `.json` contract to executable content. It cannot write
`../outside.txt`, an absolute host path, or a duplicate target. It
cannot exceed the maximum file count, per-file byte ceiling, or total
byte budget.

This is capability design expressed as data. The provider receives
authority only over the files explicitly named in the contract.

### Acceptance before execution

Acceptance checks are also declared before the provider acts. That
prevents the system from moving the goalposts after seeing the output.
The current allowlist is small and deterministic. Each check has a
stable identifier, type, target or parameters, expected value, and later
observed result.

The manifest does not attempt to encode every human expectation. A
bounded machine check should be used only when its semantics are
objective. Subjective quality stays with human review rather than being
disguised as a deterministic verdict.

### Analysis policy

APR explicitly prevents hidden reasoning and chain-of-thought from
entering the persistence contract. The manifest can state whether a
bounded reasoning summary is allowed, but raw hidden reasoning, SDK
internals, and model traces remain outside the Proof Bundle. This
protects secrets and avoids treating unverifiable internal narrative as
execution evidence.

### Manifest identity

After validation and normalization, the manifest is canonicalized and
hashed. That hash binds the later bundle to the exact contract used for
execution. Editing a title, goal, provider, artifact rule, limit, or
check changes the identity. The verifier recomputes the hash rather than
trusting the stored value.

The manifest therefore answers three questions before autonomy begins:

1.  What is expected?
2.  What is permitted?
3.  How will objective acceptance be evaluated?

An autonomous mission that cannot answer those questions cannot produce
a precise execution proof.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 8
- `src/agent_proof_runtime/mission_v1.py`
- `tests/test_build_week_manifest.py`

# Part III — From Model Output to Controlled Artifacts

## Chapter 9 — Provider Architecture

The provider boundary is where probabilistic generation enters APR. It
is also where the system deliberately limits that generation’s
authority.

Every supported provider implements one narrow conceptual
transformation:

``` text
Validated Mission
        ↓
Structured Artifact Proposal
+ Safe Provider Metadata
```

The provider does not receive a generic filesystem tool, a terminal, a
package manager, or permission to redefine the mission. This keeps the
core evidence path independent from any particular model and prevents
the most capable component from quietly becoming the runtime
administrator.

### The deterministic fixture

The fixture provider is a first-class product component. It returns
deterministic output for the same normalized mission, requires no API
key, performs no network call, and exercises the same proposal parser,
artifact policy, acceptance engine, event model, bundle builder,
verifier, report, Mission Control, and Tamper Lab as a live provider.

This is more than convenient test data. It separates two claims that are
often confused:

- the execution-evidence system behaves correctly;
- a third-party model service is currently available and returns
  acceptable output.

APR can demonstrate the first without depending on the second. CI can
reproduce the complete path. A judge can run the product in a fresh
environment. A failure in fixture mode points toward APR; a failure
limited to live mode points toward configuration, transport, provider
response, or external service behavior.

### The optional OpenAI provider

The OpenAI adapter uses the official Python SDK and Responses API with
strict JSON Schema Structured Outputs. The request sets `store=False`,
and the adapter asks the model for the same `ArtifactProposal` shape
consumed by the fixture path. The manifest or explicit CLI selection
chooses the provider; there is no silent fallback from a requested live
run to fixture mode.

`OPENAI_API_KEY` is obtained by the SDK from the process environment at
request time. It is not copied into the mission, provider metadata,
events, report, or Proof Bundle. The optional dependency is not required
for fixture execution.

The repository contains mocked tests for the official client shape,
structured response parsing, missing-key behavior, and no-secret
persistence. A later dated validation record documents one controlled
GPT-5.6 request on 2026-07-15. That run completed the declared mission
with `PASSED`, produced a `LOCAL_VERIFIED` proof, remained `UNANCHORED`,
recorded five events, and passed an exact-value scan that found no API
key in persisted run files.

That validation proves transport and integration for one controlled run.
It does not make the model a verifier, create external non-repudiation,
or certify future responses.

### Safe provider metadata

APR persists only metadata needed to identify and inspect the provider
interaction:

- provider identifier;
- requested and resolved model;
- response identifier;
- token usage;
- latency;
- input hash;
- normalized response hash;
- implementation status.

It excludes API keys, authorization headers, secret environment
variables, hidden reasoning, chain-of-thought, raw SDK objects, internal
traces, and unrelated model metadata. The raw proposal content becomes
materialized artifacts only after policy; it is not stored as an
uncontrolled provider dump.

### Failure semantics

Provider failure is its own domain. Missing credentials, missing
optional SDK, transport errors, timeouts, malformed structured output,
and unsupported provider selection should not be misreported as an
invalid manifest or failed acceptance check. Precise failure categories
make operator response possible.

The provider architecture creates a reusable seam. A future provider can
be added without weakening artifact policy or changing the verifier,
provided it returns the same bounded objects. Model choice becomes
replaceable; evidence semantics remain stable.

### Repository evidence

- `src/agent_proof_runtime/providers.py`
- `tests/test_providers.py`
- `docs/LIVE_VALIDATION.md`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` provider boundary

## Chapter 10 — Structured Artifact Proposal

A model response becomes dangerous when natural-language intent is
translated directly into host authority. APR inserts a typed proposal
between generation and side effect.

The conceptual structure is small:

``` json
{
  "artifacts": [
    {
      "path": "summary.md",
      "media_type": "text/markdown",
      "content": "..."
    }
  ]
}
```

The exact JSON Schema is derived from the validated mission. This is
important. A generic schema that accepts any relative path would leave
the runtime to discover authority after generation. APR can constrain
the model-facing schema to the declared artifact set while still
enforcing the contract independently afterward. Structured Output
improves shape; runtime policy supplies trust.

### Proposal is not execution

An `ArtifactProposal` is data. It is not a command list. The Build Week
runtime does not interpret content as shell, Python, JavaScript, package
installation, or dynamic tool instructions. It never takes a field such
as `command` and passes it to a subprocess. Text that looks like a
command remains text inside an allowed artifact, if and only if the
artifact contract permits that content type and path.

This boundary neutralizes an entire class of provider-generated side
effects. A prompt injection may still produce undesirable content, but
it cannot gain a new write path or executable host capability through
the proposal interface.

### Parsing rules

The parser rejects malformed JSON and unexpected proposal structure. It
requires a list of artifacts with the exact supported fields and types.
Empty or invalid paths, duplicate paths, unsupported media types, and
non-text content fail before materialization. The parser does not accept
an “almost correct” response by guessing what the provider intended.

Strict parsing makes provider errors visible. Repairing malformed output
silently would create ambiguity about which bytes the model returned and
which bytes the runtime invented. A later retry policy may request a
corrected proposal, but each attempt should remain a distinct,
inspectable transition.

### Why content remains untrusted

JSON Schema can validate structure, not truth. A model can return valid
JSON with incorrect content. It can satisfy a required key while writing
a poor explanation. It can remain below a byte limit while omitting
important details. APR therefore does not call schema validity
acceptance.

The proposal passes through three separate gates:

1.  syntactic and structural parsing;
2.  authorization and resource policy;
3.  deterministic acceptance after bytes exist on disk.

Each gate answers a different question. Parsing asks whether the object
is well-formed. Policy asks whether the runtime is allowed to
materialize it. Acceptance asks whether the resulting files meet
declared objective conditions.

### Proposal identity

The provider metadata contains hashes of the safe input projection and
normalized response. These values help correlate execution without
persisting secrets or raw internal traces. Artifact records later bind
the actual materialized bytes. A response hash and an artifact hash
serve different purposes: one identifies the normalized provider result;
the other proves what currently exists in the run directory.

The proposal layer is deliberately modest. It does not make a model safe
in every context. It makes one context understandable and enforceable:
proposing bounded text artifacts under a contract the model cannot
expand.

### Repository evidence

- `src/agent_proof_runtime/providers.py`
- `src/agent_proof_runtime/mission_v1.py`
- `docs/PRODUCT_BLUEPRINT.md` section 10

## Chapter 11 — Artifact Contract

The artifact contract defines the maximum write authority available to a
provider. It is the runtime equivalent of a least-privilege capability
set.

For every permitted artifact, the mission declares an exact relative
POSIX path and media type. The contract also defines required files and
global limits such as maximum file count, maximum bytes per file, and
maximum total bytes. The runtime validates the proposal against these
values even when the provider used a strict schema.

### Defense in depth

It may seem redundant to constrain the model schema and then validate
again. The redundancy is intentional. Provider-side structure is not an
authorization boundary. SDK behavior may change, a fake client may
return unexpected data, a future adapter may contain a bug, or
structured output may be decoded incorrectly. Authority is granted only
by runtime policy.

The runtime enforces:

- canonical relative paths;
- exact contract membership;
- required artifact presence;
- duplicate rejection;
- allowlisted text and media types;
- maximum file count;
- maximum per-file bytes;
- maximum total bytes;
- a fresh destination;
- exclusive file creation;
- no symbolic links;
- no arbitrary commands.

### Path safety

Path controls are easy to describe and easy to get subtly wrong.
Rejecting strings that contain `..` is not enough if normalization,
platform separators, symlinks, or encoded forms can still escape the
intended root. APR canonicalizes artifact paths as relative POSIX paths
at manifest and proposal boundaries. During materialization and
retrieval, resolved paths must remain inside the controlled root.
Symlinks are rejected rather than followed.

Exact membership is stronger than a broad pattern in this vertical
slice. If the contract declares `summary.md` and `result.json`, a
proposal for `notes/debug.txt` fails even though the path is relative
and harmless-looking. The provider may not invent authority.

### Resource boundaries

Byte and count limits prevent a validly structured proposal from
exhausting disk or memory through uncontrolled output. Limits are
evaluated against encoded bytes, not only character count, because
persistence costs bytes. Total limits matter even when every individual
file remains under its ceiling.

The Build Week path supports text artifacts, which makes encoding and
safe serving more tractable. Binary or executable artifacts would
require a broader threat model, media handling, and potentially stronger
isolation. They are not smuggled into the current profile under a
generic file abstraction.

### Materialization sequence

The controlled sequence is:

``` text
Parse proposal
-> normalize paths
-> validate exact contract membership
-> check required files, counts, and byte limits
-> create controlled directories
-> write files exclusively
-> re-read files
-> compute digests
-> record artifact evidence
```

Re-reading matters because the verifier will later evaluate bytes on
disk, not an in-memory object. The artifact record includes path, media
type, byte size, and SHA-256 digest. Those values allow independent
detection of missing, changed, or unexpected content.

### Policy failure is not provider failure

A provider can return structurally valid output that violates authority.
That is an artifact-policy failure. The distinction tells operators that
transport and parsing succeeded, but the proposal attempted something
outside the mission. In a future system, that signal may trigger
provider feedback, a human review, or a security event. It should never
be collapsed into a generic exception.

The artifact contract is where APR converts a broad model capability
into a narrow, reviewable permission surface.

### Repository evidence

- `src/agent_proof_runtime/build_week_runtime.py`
- `src/agent_proof_runtime/mission_v1.py`
- `tests/test_build_week_runtime.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` runtime policy

## Chapter 12 — Acceptance Engine

After permitted artifacts exist, APR evaluates the objective conditions
declared in the mission. The acceptance engine is deterministic by
design. A probabilistic provider may create content; it does not judge
whether its own content met the contract.

The current allowlist contains six check types:

| Check                | Question answered                                                               |
|----------------------|---------------------------------------------------------------------------------|
| `file_exists`        | Does the declared regular file exist at the safe target?                        |
| `file_count`         | Does the controlled artifact tree contain the expected number of regular files? |
| `contains_text`      | Does a text artifact contain the required literal value?                        |
| `json_valid`         | Can the artifact be decoded as a valid JSON value under the evaluator’s rules?  |
| `json_required_keys` | Is the JSON object valid and does it contain each declared key?                 |
| `maximum_size`       | Is the artifact at or below the declared byte ceiling?                          |

These checks are intentionally bounded. They require no model call,
shell, package installation, or untrusted interpreter. A check is
accepted only when it is declared in the manifest and has a supported
parameter shape.

### Evidence, not only status

Each acceptance result records a stable check identifier, check type,
pass/fail boolean, expected value, and safe observed value. The
mission’s overall acceptance status is derived from the individual
results. A failure should explain which condition did not hold rather
than returning an undifferentiated red badge.

The record is later included in the Proof Bundle, but inclusion is not
enough. The independent verifier re-reads the materialized artifacts,
reruns the deterministic evaluator, and compares the reproduced results
to the recorded acceptance evidence. Changing an acceptance status or
expected value without changing the relevant evidence should therefore
fail verification.

### Mission outcome versus proof outcome

Suppose a mission requires `result.json` to contain the keys `name` and
`score`, but the provider returns valid JSON with only `name`. The
`json_required_keys` check fails. The mission outcome is `FAILED`.

If the bundle accurately records the manifest, artifact, check result,
events, and hashes, the proof can still be `LOCAL_VERIFIED`. The
verifier is not claiming the mission succeeded. It is claiming that the
evidence of failure is internally consistent.

This distinction is one of APR’s most important design decisions.
Verification must not turn into a success-only mechanism. Failed
execution is often where reliable evidence matters most.

### Limits of deterministic acceptance

An allowlisted check proves only its exact predicate. `contains_text`
does not prove that surrounding prose is correct. `json_valid` does not
prove that values are truthful. `file_exists` does not prove usefulness.
Even a large test suite does not prove the absence of all defects.

The contract author should resist encoding subjective ideas as fake
precision. A human design review remains human. A legal conclusion
remains outside a simple JSON predicate. APR strengthens objective
checks and preserves evidence for subjective review; it does not erase
the difference.

### Extending the engine

A future check type should satisfy strict properties before entering the
allowlist:

- deterministic for the declared inputs;
- bounded in time and resources;
- safe without arbitrary execution;
- representable as structured evidence;
- independently reproducible;
- versioned so old bundles keep their meaning.

The value of the acceptance engine comes from predictable semantics, not
from the number of checks it can advertise.

### Repository evidence

- `src/agent_proof_runtime/acceptance.py`
- `src/agent_proof_runtime/validator.py`
- `tests/test_build_week_runtime.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` acceptance policy

# Part IV — The Integrity Core

## Chapter 13 — Event Model

Ordinary logs describe activity. APR events are structured inputs to an
integrity calculation. The difference is not that logs are useless; it
is that a mutable list of messages cannot by itself reveal removal,
reordering, or modification.

Every protected event contains:

- a sequential index;
- an event type;
- structured input, output, and details;
- a hash of each structured section;
- the previous event’s step hash;
- its own step hash.

The first event points to a fixed genesis value: a `sha256:` prefix
followed by thirty-two zero bytes expressed as hexadecimal. Later events
point to the exact step hash stored in their predecessor.

### Canonical bytes

Hashing JSON requires a deterministic representation. Whitespace, key
order, and number formatting can make semantically similar objects
produce different byte strings. APR uses an integer-safe subset of RFC
8785 identified as `RFC8785-JCS-INTEGER-PROFILE-v1`.

The profile serializes objects with lexicographic UTF-16 key ordering,
emits UTF-8, rejects lone UTF-16 surrogates, accepts integers only
within the IEEE-754 safe range of plus or minus 9,007,199,254,740,991,
and rejects floating-point values. These restrictions trade broad JSON
flexibility for stable cross-process hashing.

For event `i`, APR first calculates:

``` text
I_i = SHA256(canonical(input_i))
O_i = SHA256(canonical(output_i))
D_i = SHA256(canonical(details_i))
```

The step payload binds the event index, type, those three hashes, and
the previous step hash:

``` text
S_i = SHA256(canonical({
  step_index: i,
  type: type_i,
  input_hash: I_i,
  output_hash: O_i,
  details_hash: D_i,
  previous_step_hash: S_(i-1)
}))
```

The actual implementation hashes a canonical JSON object with named
fields rather than a positional tuple, but the dependency is the same.

### What the chain detects

If an event’s input, output, or details change, its section hash
changes. That changes the step hash. The next event’s
`previous_step_hash` no longer points to the recomputed value. Removing
or reordering events also breaks sequential indices and linkage. Adding
unknown fields or deleting required fields fails exact schema checks.

The verifier performs these calculations from event content. It does not
compare only the stored step hashes to each other.

### Build Week event sequence

A fixture mission with two artifacts records five significant
transitions:

1.  `runtime.mission_started`;
2.  `provider.artifact_proposal_received`;
3.  one `runtime.artifact_materialized` event per artifact;
4.  `runtime.acceptance_completed`.

The sequence is compact on purpose. An evidence stream should capture
security- and verification-relevant transitions without becoming a dump
of every debug message. Operational logs may remain useful outside the
bundle, but verification facts need stable structured semantics.

### Merkle aggregation

APR turns event step hashes into a Merkle root using RFC 6962-style
domain separation. An empty tree hashes the empty byte string. A leaf
hashes the byte `0x00` followed by the decoded step-hash bytes. An
internal node hashes `0x01` followed by its left and right child hashes.
Non-power-of-two trees split at the largest power of two smaller than
the leaf count.

The linear chain and Merkle root are related but not identical. The
chain makes order and predecessor linkage explicit. The root gives a
compact commitment to the complete ordered leaf set and prepares the
architecture for future inclusion-proof work. The current bundle does
not claim an external transparency log merely because it has a Merkle
root.

### Repository evidence

- `src/agent_proof_runtime/canonical.py`
- `src/agent_proof_runtime/chain.py`
- `src/agent_proof_runtime/merkle.py`
- `tests/test_chain_merkle.py`

## Chapter 14 — Proof Bundle

The Proof Bundle is APR’s primary product artifact: a versioned,
portable execution receipt designed to remain useful outside the runtime
and Mission Control.

Build Week uses `apr.proof-bundle.v1`. The repository’s verifier also
preserves support for `apr.proof-bundle.v0.1` and `.v0.2`. Version
dispatch is essential because evidence semantics cannot be changed
retroactively without invalidating old receipts or, worse, interpreting
them under rules they never claimed to satisfy.

### Bundle anatomy

The v1 bundle contains seven major evidence areas:

| Section          | Purpose                                                                                    |
|------------------|--------------------------------------------------------------------------------------------|
| `schema_version` | Selects the exact verification semantics.                                                  |
| `mission`        | Stores the canonical manifest and its recomputable hash.                                   |
| `provider`       | Stores allowlisted provider metadata and interaction hashes.                               |
| `run`            | Identifies the run, backend, security level, network policy, and timing.                   |
| `events`         | Carries the ordered hash-linked execution record.                                          |
| `artifacts`      | Records relative paths, media types, sizes, and SHA-256 digests.                           |
| `acceptance`     | Carries mission outcome and individual deterministic results.                              |
| `verification`   | Records the runtime’s claimed local status as a claim to check.                            |
| `integrity`      | Declares canonicalization, algorithm, counts, Merkle root, bundle hash, and anchor status. |

The bundle stores the complete normalized Mission Manifest rather than
only a mission identifier. Portability requires enough context to
understand what was supposed to happen. It stores artifact metadata
rather than embedding every file; the verifier resolves referenced
artifacts relative to the bundle’s run directory.

### The whole-bundle hash

The bundle hash commits to the verification-relevant document. APR
computes it from a canonical representation that excludes the
bundle-hash field itself according to the versioned bundle logic. The
verifier applies the same exclusion rule and recomputes the digest.

This hash detects changes to critical metadata that artifact and event
hashes alone might not cover: mission fields, provider values, run
properties, acceptance records, event count, Merkle root, anchor status,
or the claimed verification state.

A self-contained hash is not an external signature. If an attacker
replaces the document and recomputes the hash, a local verifier sees a
consistent new bundle. External anchoring or signing is required to
prove that a particular historical hash existed outside the attacker’s
control.

### Portable does not mean context-free

To re-verify a bundle, a recipient needs the bundle and its referenced
artifact tree. The verifier does not need the original Mission Control
process or provider connection. It also does not need the API key or raw
model response. This is a deliberate privacy and operational boundary:
proof should contain what is necessary for its claims, not every piece
of sensitive execution state.

### Conservative status language

The bundle’s anchor field is `UNANCHORED`. The runtime security level is
`development-only` for the controlled-artifact path. These values travel
with the evidence so that a copied bundle cannot be separated easily
from its limitations.

The Proof Bundle is therefore not a certificate that the world should
trust an agent. It is a structured receipt that lets another process
check precise execution claims under a declared model.

### Repository evidence

- `src/agent_proof_runtime/bundle.py`
- `src/agent_proof_runtime/build_week_runtime.py`
- `src/agent_proof_runtime/validator.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` schemas

## Chapter 15 — Independent Verifier

The independent verifier is the component that turns APR from a
recording system into a verification system. Its foundational rule is
simple:

> Never trust a status merely because the runtime wrote it.

The verifier receives the path to a Proof Bundle. It parses the JSON,
identifies the schema version, applies the exact supported shape,
resolves the run directory, and derives its own result. A successful
runtime is not a prerequisite for a successful verification; a
faithfully recorded failed mission may still produce valid evidence.

### Verification sequence

For a v1 bundle, the verifier performs a layered replay:

1.  Validate top-level and nested key sets.
2.  Validate supported schema and data types.
3.  Recompute the canonical Mission Manifest hash.
4.  Validate safe provider metadata shape and consistency.
5.  Resolve each artifact under the run root.
6.  Reject absolute paths, traversal, missing files, unknown files, and
    symlinks.
7.  Re-read bytes and recompute size and SHA-256.
8.  Validate event fields and sequential indices.
9.  Recompute input, output, details, and step hashes.
10. Rebuild previous-step linkage.
11. Recompute the RFC 6962-style Merkle root.
12. Reproduce deterministic acceptance checks from the artifacts.
13. Compare reproduced results with recorded evidence and mission
    status.
14. Recompute the bundle hash.
15. Cross-check event counts, security labels, and other critical
    metadata.

Any mismatch contributes a concrete failure reason. The verifier should
fail as a result, not crash as an exception, when it receives corrupted
evidence. The repository records one illustrative hardening change:
invalid UTF-8 introduced by artifact tampering originally escaped as an
exception; the boundary was changed to return `FAILED`, and a regression
test was added.

### Exact shapes matter

Unknown fields are not harmless in evidence formats. They may carry a
second status or an alternative interpretation ignored by one verifier
and trusted by another. APR uses exact key sets for supported schemas.
Missing and unknown fields are reported rather than silently normalized.

### Independence and shared deterministic logic

The verifier can reuse a pure deterministic acceptance evaluator without
trusting the runtime’s stored output. Independence does not require
rewriting every mathematical rule in a different language. It requires
independently reading the source evidence and deriving the result rather
than accepting the executor’s conclusion.

For stronger assurance, the long-term roadmap can add independently
implemented verifiers, published test vectors, and external execution.
The current architecture already makes that possible because the bundle
is versioned and portable.

### Failure as useful output

A good verifier says more than `false`. It tells the operator that an
artifact hash mismatched, an event no longer pointed to its predecessor,
the Merkle root differed, the bundle hash was wrong, an acceptance
record could not be reproduced, or a path was unsafe. Precise error
output supports audit, debugging, and incident response.

The verifier’s authority is still bounded. It determines evidence
integrity. It does not determine whether the artifact is strategically
wise, legally sufficient, or ready to deploy. That decision belongs to
the operator.

### Repository evidence

- `src/agent_proof_runtime/validator.py`
- `tests/test_validator_tampering.py`
- `tests/test_build_week_runtime.py`
- `docs/CODEX_COLLABORATION.md`

## Chapter 16 — Mission Control

Cryptographic evidence is valuable only when operators can understand
and use it. Mission Control provides a human-facing view over APR’s
existing runner and verifier. It does not replace either component and
does not invent a new source of truth.

The interface exposes approved checked-in missions, provider selection,
mission status, proof status, anchor status, safe provider metadata,
artifacts and hashes, acceptance checks, event replay, bundle hash,
Merkle root, generated report, raw bundle, re-verification, and Tamper
Lab. The central design rule is:

> Every security or execution claim in the interface must map to bundle
> evidence, verifier output, or runtime state with an explicit
> limitation.

### Thin adapter, shared semantics

Mission Control calls the same mission loader, runtime, and verifier
used by the CLI. A UI-only verification algorithm would risk divergence.
A green badge derived from server state instead of bundle replay would
weaken the product’s central claim.

The interface separates mission, proof, and anchor status. This prevents
an acceptance failure from being mistaken for evidence corruption and
prevents local integrity from being presented as external anchoring.

### Constrained public surface

The HTTP application is a small standard-library Python service with
static frontend assets. It allows checked-in or explicitly approved
missions rather than arbitrary host paths. Public execution defaults to
fixture mode. Optional OpenAI execution uses server-side configuration;
credentials never reach browser code.

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
authentication. The project therefore describes hosted Mission Control
as a single-operator demo, not a multi-tenant production control plane.

### Operational honesty

The public Railway validation recorded one operational edge case. After
an automatic redeploy, a stale browser tab held a CSRF token from the
previous process and received `request token is missing or invalid`.
Reloading obtained the new token and restored normal operation. The
control was not disabled to make the demo pass.

This is the kind of detail evidence-oriented products should preserve. A
successful hosted validation includes the constraints and observed
recovery behavior, not only a screenshot of the healthy state.

### Mission Control is not the proof

An operator can download or inspect the bundle and verify it through the
CLI. If Mission Control disappears, the receipt still has meaning. This
portability keeps the user interface in its proper role: explanation and
operation, not monopoly over truth.

### Repository evidence

- `src/agent_proof_runtime/mission_control.py`
- `src/agent_proof_runtime/mission_control_ui.py`
- `tests/test_mission_control.py`
- `tests/test_mission_control_build_week.py`
- `docs/HOSTED_VALIDATION.md`

# Part V — Making Failure Visible

## Chapter 17 — Tamper Lab

Integrity systems are easiest to understand when users can watch them
fail. Tamper Lab turns APR’s abstract protection claims into a
controlled experiment.

The lab begins with an existing run and its Proof Bundle. It
fingerprints every file in the original run, creates a temporary copy,
applies one supported mutation to the copy, invokes the same independent
verifier used elsewhere, captures the exact failure reasons, and deletes
the copy. It then fingerprints the original again and confirms that the
source evidence did not change.

The current lab supports three cases:

1.  **Artifact tampering** changes materialized file content.
2.  **Event tampering** changes protected event data.
3.  **Metadata tampering** changes critical bundle metadata.

Each case targets a different integrity layer.

### Artifact tampering

When artifact bytes change, the recorded size or SHA-256 no longer
matches. The verifier re-reads the file and reports the discrepancy.
Depending on the artifact, the reproduced acceptance evidence may also
change. The event record and bundle hash still bind the original values,
creating multiple observable inconsistencies.

### Event tampering

Changing an event’s input, output, details, or type changes its
canonical section hash or step hash. Later predecessor linkage breaks,
and the Merkle root no longer matches the recomputed leaf set. The
verifier reports the concrete chain and integrity failures rather than
assuming the stored hashes are authoritative.

### Metadata tampering

Critical metadata may sit outside artifact bytes and event content.
Changing a manifest value, provider field, run property, acceptance
record, anchor label, event count, Merkle root, or bundle-level field
should be caught by schema, cross-field, or whole-bundle checks. This
case demonstrates why a bundle hash is needed in addition to artifact
hashes.

### Copy-on-tamper is a safety rule

The lab never modifies the original evidence. This is not merely
convenient for a demo. Security testing must not destroy the object it
is supposed to evaluate. The before-and-after fingerprint makes original
preservation itself observable.

CLI examples are direct:

``` bash
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case artifact
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case event
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case metadata
```

The expected contrast is:

``` text
Original run: LOCAL_VERIFIED
Tampered copy: FAILED
```

Tamper Lab does not prove resistance to a fully privileged attacker who
replaces the entire local system and recomputes every value. It proves
that supported modifications become visible to the independent verifier
when evaluated against the preserved receipt and rules.

The product lesson extends beyond APR: if a verification mechanism
cannot demonstrate a controlled negative case, users have little basis
for understanding what its positive result means.

### Repository evidence

- `src/agent_proof_runtime/tamper_lab.py`
- `tests/test_build_week_runtime.py`
- `docs/PRODUCT_BLUEPRINT.md` section 17

## Chapter 18 — CLI Product Surface

APR’s command-line interface is the transparent automation surface
beneath Mission Control. It supports direct execution, independent
verification, tamper experiments, backend diagnostics, and legacy
compatibility.

### Fixture-first judge path

A fresh Python 3.11 or 3.12 environment can run the complete
deterministic flow:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

apr mission validate examples/build-week-mission.json
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/build-week-demo
apr verify .runs/build-week-demo/proof-bundle.json
```

The expected result is a mission `PASSED`, proof `LOCAL_VERIFIED`, and
anchor `UNANCHORED`. No key, network call, or optional SDK is required.

### Optional live provider

The live adapter is installed separately:

``` bash
python -m pip install -e '.[openai]'
```

When `OPENAI_API_KEY` is already configured in the process environment,
the same mission can select the OpenAI provider:

``` bash
APR_OPENAI_MODEL=gpt-5.6 apr run examples/build-week-mission.json \
  --provider openai \
  --output .runs/gpt-5-6-smoke
```

Missing credentials fail clearly. APR does not create, request, print,
store, or silently replace the key. A requested OpenAI run does not fall
back to fixture mode.

### Independent verification

`apr verify` accepts a bundle path and produces an exit status suitable
for scripts. The verifier is version-aware, so legacy v0.1 and v0.2
receipts remain valid under their own semantics while v1 uses the Build
Week path.

### Legacy compatibility

The original proof slice remains available:

``` bash
apr demo --output .runs/legacy-demo
apr verify .runs/legacy-demo/proof-bundle.json
```

MissionSpec v0.2 and its execution path also remain preserved. Backward
compatibility is a product invariant, not an incidental test.

### Mission Control and diagnostics

The interface starts with:

``` bash
apr mission-control
```

`PORT` is honored, and host/port options can be passed explicitly.
Binding beyond loopback requires deliberate remote opt-in because the
service does not claim multi-user authentication.

Backend diagnosis is separate from execution:

``` bash
apr doctor --backend gvisor
```

On a machine without Docker and registered `runsc`, the correct result
is unavailable. The command must not substitute `runc` and report a
false gVisor success.

### Exit codes as an API

A CLI is not reliable automation if every failure looks the same. APR
distinguishes successful execution from invalid input, provider failure,
policy rejection, acceptance failure, verification failure, and
operational startup failure. Human- readable messages explain the
domain; exit codes let scripts react.

The CLI keeps the evidence system usable without a browser and makes
every central claim reproducible from commands that can run in CI.

### Repository evidence

- `src/agent_proof_runtime/cli.py`
- `tests/test_cli_build_week.py`
- `README.md`
- `docs/BUILD_WEEK.md`

## Chapter 19 — HTTP Surface

Mission Control’s HTTP layer is intentionally smaller than a general web
platform. It exposes the operations required for a safe judge and
operator path while refusing broad host authority.

The server supports health status, approved mission listing, constrained
mission execution, run discovery, run detail, independent
re-verification, report and Proof Bundle retrieval, declared artifact
retrieval, and disposable tamper actions. Its static frontend renders
those capabilities without adding separate verification semantics.

### Health

`GET /health` provides a low-cost operational probe. In the hosted
validation, it returned:

``` json
{
  "ok": true,
  "status": "healthy",
  "service": "apr-mission-control",
  "version": "0.3.0"
}
```

Health means the checked-in service started and responded. It does not
prove that every mission will pass, that run storage is durable, or that
an external anchor exists.

### Request constraints

State-changing operations require a same-origin CSRF token. Request
bodies are bounded. Host headers are validated to reduce DNS-rebinding
risk. Content Security Policy limits the browser execution surface. Run
names and paths are normalized and validated. File retrieval resolves
targets beneath an approved root, rejects traversal and symlinks, and
serves only constrained content.

The service does not accept an arbitrary shell command or filesystem
path from a browser. Missions are discovered from an approved checked-in
directory and parsed under the same strict schema used by the CLI.

### Binding policy

Loopback is the default. Remote binding requires an explicit
`--allow-remote` flag. That flag changes reachability, not identity. It
does not add accounts, roles, sessions, rate limits, or tenant
isolation. A remote deployment must therefore be described as a
controlled single-operator or competition demonstration.

### Evidence retrieval

Reports and raw bundles are useful because different users need
different levels of detail. The HTML report summarizes the run. Mission
Control offers interactive views. The JSON bundle remains the
machine-verifiable source. Artifact endpoints serve only files
referenced by the safe run structure.

### Hosted state

Run storage is local filesystem state and may be ephemeral on hosted
platforms. A restart or redeploy can remove evidence unless the operator
attaches appropriate persistent storage. The book treats durability as
an operational choice, not an implicit guarantee of deployment.

The HTTP layer succeeds when it makes the existing evidence path
accessible without expanding the runtime into a generic remote execution
service.

### Repository evidence

- `src/agent_proof_runtime/mission_control.py`
- `tests/test_mission_control.py`
- `docs/HOSTED_VALIDATION.md`

## Chapter 20 — Repository Architecture

APR’s repository architecture follows a deliberate constraint: do not
introduce distributed infrastructure before the product requires it.

The current system is one Python package with a standard-library
runtime. The official OpenAI SDK is an optional dependency used only
when live provider selection requires it. Mission Control uses the
standard library HTTP stack and static assets. This keeps installation,
test setup, deployment, and audit surface small.

Conceptually, the package contains:

``` text
agent_proof_runtime/
├── CLI and mission loading
├── strict mission validation
├── fixture and OpenAI providers
├── controlled artifact runtime
├── artifact policy
├── deterministic acceptance engine
├── canonical serialization
├── event chain and Merkle construction
├── Proof Bundle builder
├── version-aware independent verifier
├── Mission Control server and static UI
├── Tamper Lab
├── reports
└── legacy and gVisor execution paths
```

The repository root adds checked-in mission examples, test suites,
architecture and validation documents, a Dockerfile, Railway
configuration, CI workflow, and this book.

### Why one package

The product’s hard problem is evidence semantics, not service
orchestration. Splitting the runner, verifier, UI, and storage into
separate deployed services too early would add network authentication,
version coordination, retries, queues, and state consistency before
those components provide independent trust.

A monolithic package does not prevent logical separation. Providers
implement a narrow interface. The verifier has version-aware entry
points. Mission Control adapts existing functions. The gVisor backend
has an explicit diagnostic boundary. These seams can become processes
later if product requirements justify it.

### Dependency discipline

Narrow dependencies reduce supply-chain and compatibility risk. Fixture
execution and verification should not fail because a model SDK is
unavailable. The optional OpenAI extra makes that boundary visible at
installation time.

The project supports Python 3.11 and 3.12. Test commands can run through
`unittest` with `PYTHONPATH=src`, and normal editable installation
exposes the `apr` command.

### GitHub as project history

The repository documents preserved implementation checkpoints and avoids
rewriting the Build Week lineage. Earlier bundle versions remain
testable. The current active work lives on the Build Week branch rather
than pretending that unmerged work is already present on `main`.

This provenance matters for an evidence product. Architecture decisions,
validation records, code, tests, and book claims should be traceable to
preserved source rather than reconstructed after the fact.

### Repository evidence

- `pyproject.toml`
- `docs/PRODUCT_BLUEPRINT.md` section 20
- `docs/BEFORE_BUILD_WEEK.md`
- `docs/BUILD_WEEK_CHANGELOG.md`

# Part VI — Operating the System Honestly

## Chapter 21 — Execution Backends

APR preserves several execution profiles because proof generation and
workload isolation are separate concerns. A system can produce
internally consistent evidence while running behind a weak isolation
boundary. Stronger isolation can reduce runtime risk without
automatically creating external trust in the receipt.

### Controlled-artifact runtime

The Build Week v1 path does not execute model-generated code or shell
commands. It accepts a structured proposal and writes allowlisted text
artifacts. Its run metadata labels the backend
`controlled-artifact-runtime`, the security level `development-only`,
and the network policy either `fixture-offline` or `provider-api-only`.

This profile gains safety by refusing general execution capability. It
is suitable for demonstrating mission contracts, provider boundaries,
artifact policy, acceptance evidence, Proof Bundles, and independent
verification. It is not a sandbox for hostile arbitrary code.

### Local demonstration backend

The earlier MissionSpec v0.2 path includes `local-demo`, which runs only
the worker shipped with APR. It does not accept an arbitrary command and
retains the `development-only` label. Its purpose is to exercise the
full Mission Runner flow on a machine without Docker.

The legacy local-process harness reduces the environment, applies
timeouts and basic resource controls where available, and uses
disposable workspaces. Those controls are useful operational hygiene,
but they do not block network access or protect the host from malicious
code.

### Docker + gVisor

MissionSpec v0.2 also defines a hardened `gvisor` backend. Its contract
requires:

- Docker with the `runsc` runtime registered;
- a container image pinned by SHA-256 digest;
- `--pull=never` to prevent implicit image replacement;
- `--network=none`;
- a read-only root filesystem;
- dropped Linux capabilities;
- `no-new-privileges`;
- memory, CPU, PID, and timeout limits;
- a copied source tree mounted read-only;
- writes limited to `/output` and ephemeral `/tmp`;
- artifact count and byte monitoring during execution.

The adapter is fail-closed. If Docker, `runsc`, the pinned image, or
another required condition is unavailable, execution stops. It does not
use ordinary Docker while reporting a gVisor security level.

The repository contains adapter implementation and simulated tests. The
recorded environment did not include `runsc`, so real gVisor execution
remains unvalidated. The correct present-tense claim is therefore:
implemented and fail-closed, but not real-runtime validated.

### Isolation versus evidence trust

Even a correctly functioning gVisor boundary would not solve external
non-repudiation. It can constrain a workload relative to the host
kernel, but the host that stores the bundle may still alter local
evidence. Conversely, an external signature over a bundle would not
prove that the workload was safely isolated.

APR tracks these axes separately:

| Axis                | Current question                                                |
|---------------------|-----------------------------------------------------------------|
| Workload capability | Text proposal only, built-in demo worker, or container command? |
| Isolation           | Development-only process boundary or validated sandbox?         |
| Network policy      | Offline, provider-only, or blocked?                             |
| Evidence integrity  | Does the bundle recompute locally?                              |
| External trust      | Is the bundle signed or anchored outside the host?              |

This separation prevents a container label, a hash, or a hosted URL from
carrying security meaning it does not actually possess.

### Repository evidence

- `docs/ARCHITECTURE_LOCK_v0.2.md`
- `src/agent_proof_runtime/gvisor.py`
- `tests/test_gvisor.py`

## Chapter 22 — Deployment Blueprint

APR’s competition deployment favors a simple containerized service:

``` text
Checked-in repository
        ↓
Docker image
        ↓
Railway or controlled Linux host
        ↓
Mission Control
        ↓
Fixture enabled by default
        ↓
Optional OpenAI provider through server environment
```

The checked-in Dockerfile uses Python 3.12 slim, installs the package,
creates a non-root user with UID 10001, prepares the run directory,
exposes port 8080, and defines an HTTP health probe. The container
starts Mission Control on `0.0.0.0` with explicit remote opt-in.

Railway configuration selects the Dockerfile builder, uses `/health`,
restarts on failure within a finite policy, and starts the same Mission
Control command. This is a small deployment surface with no mandatory
database migration.

### Fixture as the public default

Public judging should not depend on a secret or third-party service.
Fixture mode allows every user to exercise the complete evidence path.
It also makes cost, availability, and rate limits irrelevant to the core
demonstration.

If live provider access is enabled, `OPENAI_API_KEY` belongs only in the
backend environment. It must never appear in frontend JavaScript,
repository files, downloaded artifacts, reports, bundles, screenshots,
or example documentation. The browser chooses only from server-allowed
operations; it never receives the secret.

### Persistence

APR stores runs on the local filesystem. On many application platforms
that storage is ephemeral. A restart, migration, or redeploy may remove
prior evidence. The current hosted product states this limitation rather
than implying durable audit retention.

When evidence must survive, operators should attach an appropriate
persistent volume or export bundles and artifacts to a controlled store.
Strong retention will also require lifecycle rules, access control,
encryption, backup, and deletion policy—requirements outside the current
competition slice.

### Rollback

The deployment avoids mandatory state migrations, so application
rollback is straightforward:

1.  restore the previous image or repository revision;
2.  restart the stateless service;
3.  preserve externally exported evidence independently;
4.  verify `/health` and rerun the deterministic fixture path.

A rollback should not rewrite historical Proof Bundles. Version-aware
verification allows older receipts to retain their semantics even when
the application version changes.

### Observed hosted validation

The repository records a public Railway deployment at
`https://agent-proof-runtime-production.up.railway.app`. The health
endpoint returned version `0.3.0`, the deterministic mission passed, the
proof remained `LOCAL_VERIFIED` and `UNANCHORED`, all three tamper cases
failed as expected, the untouched original re-verified, and the report
opened successfully.

That observation validates the checked-in deployment path and public
judge flow. It does not create multi-user authentication, durable
storage, hostile-code isolation, or external anchoring.

### Repository evidence

- `Dockerfile`
- `railway.json`
- `docs/HOSTED_VALIDATION.md`
- `docs/PRODUCT_BLUEPRINT.md` section 22

## Chapter 23 — Testing Strategy

APR’s test strategy mirrors its trust model. The project does not treat
one passing end-to-end demo as sufficient evidence. It tests contracts,
deterministic logic, negative cases, compatibility, operational
interfaces, and failure containment.

### Test categories

The repository covers:

- canonicalization unit tests;
- event-chain and Merkle tests;
- strict manifest contract tests;
- proposal and artifact-policy tests;
- deterministic fixture reproducibility;
- acceptance-engine behavior;
- mocked OpenAI structured output;
- missing-key and no-secret persistence;
- Proof Bundle v0.1, v0.2, and v1 verification;
- artifact, event, and metadata tampering;
- original-run preservation;
- CLI integration and exit behavior;
- Mission Control HTTP safety;
- health and artifact retrieval;
- gVisor fail-closed command construction;
- end-to-end fixture execution.

CI runs on Python 3.11 and 3.12. It installs the package, executes the
unit suite, validates checked-in missions, runs legacy and Build Week
fixture missions, verifies their bundles, and checks the Mission Control
command surface. No live API call is required by default.

### Negative tests are product tests

For a verification system, rejection behavior is at least as important
as the happy path. Tests should prove that unknown fields, duplicate
JSON keys, unsafe paths, un-pinned images, missing `runsc`, oversized
artifacts, malformed provider output, symlinks, incorrect hashes, broken
chains, wrong Merkle roots, inconsistent acceptance evidence, and
tampered metadata do not pass silently.

An adversarial test should assert the exact failure domain when
practical. A generic exception may hide that the wrong layer caught the
problem or that the public API crashed instead of returning `FAILED`.

### Determinism

The fixture provider allows byte-level reproducibility. Given the same
normalized mission, it should produce the same proposal and traverse the
same evidence contracts. Run IDs and timestamps may vary as operational
metadata, but deterministic content and checks make regression analysis
possible.

Canonicalization and Merkle logic benefit from fixed vectors. As
interoperability grows, published cross-language vectors will become
necessary so independent implementations can prove identical behavior.

### Mocked versus live tests

Mocked provider tests answer whether APR constructs the expected SDK
request, parses the expected response shape, handles missing
configuration, and avoids persistence of injected secret values. They do
not prove external transport.

A controlled live test answers the narrower transport question. The
repository’s dated record documents one successful GPT-5.6 run after the
fixture flow and local suite were complete. Live tests remain opt-in
because they require secrets, network, cost, and external availability.

### Validation hierarchy

The strongest practical workflow is cumulative:

``` text
unit contracts
-> negative/adversarial cases
-> fixture integration
-> independent verification
-> container judge path
-> hosted smoke test
-> controlled live provider test
```

No higher layer erases a lower-layer failure. A healthy deployment
cannot compensate for a broken verifier test.

### Repository evidence

- `tests/`
- `.github/workflows/ci.yml`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 24 — Observability and Evidence

Observability and evidence overlap, but they are not synonyms.
Observability helps operators understand a running system through logs,
metrics, and traces. Evidence supports a later, bounded verification
claim.

An operational log may record retries, debug messages, stack traces, and
request context. That information can be valuable during an incident,
but it may be noisy, mutable, environment-specific, and unsafe to
distribute. A Proof Bundle should contain only structured facts required
for its versioned verification semantics.

### Evidence over opaque logs

APR represents verification-relevant facts explicitly:

- mission and manifest hash;
- provider identity and safe interaction metadata;
- artifact paths, media types, sizes, and digests;
- deterministic acceptance expectations and observations;
- ordered event inputs, outputs, details, and hashes;
- Merkle root and whole-bundle hash;
- run identity, timing, backend, network, and security labels;
- proof claim and anchor state.

This structure allows the verifier to recompute rather than search text
logs for a success message.

### Safe observability

More telemetry is not automatically better. APR excludes credentials,
raw authorization values, hidden reasoning, chain-of-thought, unrelated
environment variables, and uncontrolled SDK objects. Provider metadata
is allowlisted. Input and response hashes support correlation without
retaining every internal detail.

Privacy and verifiability can reinforce each other when the evidence
contract is minimal. A future regulated profile will need explicit PII
handling, retention, and redaction rules, but the current product
already rejects the idea that every model trace belongs in permanent
evidence.

### Correlation

The system exposes several stable identifiers for different layers:

- mission ID identifies the declared task;
- manifest hash identifies the exact normalized contract;
- run ID identifies one execution;
- provider response ID identifies the external response where available;
- event indices and step hashes identify transitions;
- bundle hash identifies the receipt state.

Using the right identifier prevents confusion between rerunning the same
mission and replaying the same evidence. Two runs may share a mission
hash while having distinct run IDs, timestamps, provider response IDs,
and bundle hashes.

### Explainability without hidden reasoning

APR does not require chain-of-thought to explain execution. The manifest
explains the declared objective. Events explain transitions. Artifacts
show outputs. Acceptance records show objective evaluation. Provider
metadata identifies the interaction. The report and Mission Control
organize this evidence for a human.

This is operational explainability based on observable state, not an
attempt to turn a model’s private reasoning into a trusted transcript.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 24
- `docs/PROJECT_MANIFESTO.md` section 8
- `src/agent_proof_runtime/build_week_runtime.py`

# Part VII — Evaluation and Differentiation

## Chapter 25 — Failure Model

APR treats failure as a structured outcome rather than a single
exception class. The stage at which a mission fails determines what
evidence exists, which component needs attention, and whether a Proof
Bundle can still be valid.

### Manifest failure

The requested mission violates schema or policy before provider
execution. Examples include unknown fields, duplicate JSON keys, unsafe
paths, unsupported media types, invalid limits, malformed checks, or an
unsupported schema version.

The remedy belongs to the Mission Author. The provider should not be
called because the contract is not valid enough to grant authority.

### Provider failure

The provider is unavailable, misconfigured, unauthorized, timed out,
missing its optional dependency, or returned malformed structured
output. The mission itself may be valid, but no acceptable proposal
exists.

APR reports this domain explicitly. A requested OpenAI execution must
not pretend to succeed through a fixture fallback, because that would
change the declared experiment.

### Policy failure

The proposal is structurally valid but violates the artifact contract.
It may contain an undeclared path, duplicate target, wrong media type,
missing required file, too many files, or excessive bytes. This is
neither a transport error nor an acceptance failure. The runtime refused
authority before materialization.

### Acceptance failure

The runtime safely materialized permitted artifacts, but one or more
declared objective checks did not pass. The mission outcome is `FAILED`.

This failure can still produce a `LOCAL_VERIFIED` proof. The verifier
confirms that the failed checks, artifacts, events, and hashes were
recorded consistently. A faithful receipt of failure is often more
valuable than a success message without evidence.

### Verification failure

The evidence is missing, malformed, unsafe, inconsistent, unsupported,
or modified. Examples include an artifact digest mismatch, missing file,
symlink, broken event link, wrong Merkle root, changed acceptance
record, incorrect bundle hash, or unsupported schema. The proof result
is `FAILED`, regardless of how useful the artifact appears.

Verification failure should stop downstream trust decisions. It does not
automatically reveal whether the cause was malicious tampering,
accidental corruption, incomplete copying, or a software defect. It
establishes that the available evidence cannot support the claimed
consistency.

### Operational failure

The server cannot bind, the output directory already exists, the
filesystem is unavailable, a container cannot start, the required
backend is missing, or another environmental condition blocks execution.
These failures belong to operation rather than mission semantics.

### A failure matrix

| Domain       |    Contract valid? |        Artifacts may exist? | Acceptance meaningful? |                                 Proof may be valid? |
|--------------|-------------------:|----------------------------:|-----------------------:|----------------------------------------------------:|
| Manifest     |                 No |                          No |                     No |                               Usually no run bundle |
| Provider     |                Yes |                  Usually no |                     No | Failure evidence may be recorded in future profiles |
| Policy       |                Yes | No committed run in v1 path |                     No |                              No completed v1 bundle |
| Acceptance   |                Yes |                         Yes |            Yes, failed |                      Yes, `LOCAL_VERIFIED` possible |
| Verification | Unknown or changed |                       Maybe |                  Maybe |                                        No, `FAILED` |
| Operational  |              Maybe |               Maybe partial |                  Maybe |                       Depends on completed evidence |

Precise failure semantics prevent unsafe recovery. Retrying a provider
timeout may be appropriate. Retrying an unsafe path without changing the
contract is not. Deploying an acceptance-failed artifact requires a
human decision. Ignoring a verification failure defeats the product.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 25
- `src/agent_proof_runtime/cli.py`
- `src/agent_proof_runtime/validator.py`

## Chapter 26 — Product Metrics

Early APR success is not measured by user growth or the number of
integrations. It is measured by whether the core evidence loop is
understandable, reproducible, and honest.

### Reliability metrics

Useful initial measures include:

- percentage of valid fixture missions that produce a complete bundle;
- independent verification success rate for untouched runs;
- detection rate for supported tamper classes;
- backward-compatibility success across v0.1, v0.2, and v1 receipts;
- manifest rejection accuracy for invalid and unsafe fixtures;
- provider proposal parsing failure rate;
- acceptance reproduction agreement between runtime record and verifier;
- number of secrets found in persisted evidence, with a target of zero.

The secret metric is absolute. An average close to zero is not
acceptable for API keys. Tests should use sentinel values and scan all
persisted outputs. Controlled live validation should remove process
environment values immediately after the run and record only that the
scan passed, never the secret itself.

### Performance metrics

For the deterministic path, median mission duration and independent
verification duration help detect regressions. Time to first verified
run is more useful than raw throughput during evaluation. A judge should
not wait through infrastructure that does not contribute to
understanding.

Performance should not be optimized by weakening checks. If a bundle
verifies faster because acceptance reproduction or artifact scanning was
removed, the metric has become detached from product value.

### Usability metrics

APR’s Build Week product has a concrete comprehension goal:

> Can a new evaluator execute, inspect, verify, tamper, and re-verify
> the complete flow within five minutes?

Additional useful observations include:

- whether the evaluator can explain the difference between mission and
  proof status;
- whether `UNANCHORED` is visible without reading source code;
- whether a tamper failure names the modified layer;
- whether the raw bundle can be located and verified outside the UI;
- whether the fixture path works without configuration.

These are not vanity metrics. They test whether the trust model survives
contact with a real operator.

### Security-claim metrics

Claim discipline can itself be evaluated. Every present-tense security
label should map to code and validation. Every roadmap capability should
be marked as such. A deployment should report its storage and
authentication limits. A backend should not be called gVisor-validated
without a real `runsc` run.

One useful governance metric is the number of claims that exceed
evidence. The target is zero.

### Metrics after external anchoring

Future phases may add anchor submission success, inclusion-proof
verification, signature validation, key rotation coverage, timestamp
latency, revocation behavior, and independent verifier interoperability.
Those metrics should appear only when the corresponding mechanisms
exist.

APR begins by measuring the behavior it can actually reproduce. That is
consistent with the product’s central doctrine: evidence before
confidence.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 26
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 27 — Build Week Judge Path

The judge path compresses the product into one reproducible story. Its
purpose is not to hide complexity. It is to reveal the central contract,
evidence, and failure behavior before an evaluator chooses to inspect
deeper layers.

### Step 1: Start from a deterministic environment

Install the package in Python 3.11 or 3.12 without the optional model
SDK:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Step 2: Validate the mission

``` bash
apr mission validate examples/build-week-mission.json
```

The operator sees that the contract is accepted before execution. The
checked-in mission is safe, finite, and requires no secret.

### Step 3: Run the fixture path

``` bash
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/judge-demo
```

The fixture traverses the same proposal, policy, materialization,
acceptance, event, bundle, verification, and report path used by the
live adapter.

### Step 4: Verify outside the UI

``` bash
apr verify .runs/judge-demo/proof-bundle.json
```

Expected labels:

``` text
Mission: PASSED
Proof:   LOCAL_VERIFIED
Anchor:  UNANCHORED
```

This establishes that Mission Control will visualize an independently
verified receipt rather than inventing the result.

### Step 5: Open Mission Control

``` bash
apr mission-control
```

The evaluator opens the loopback address, selects the run, and inspects:

- the trust-boundary notice;
- mission and provider;
- generated artifacts and hashes;
- deterministic acceptance checks;
- event sequence and replay;
- Merkle root and bundle hash;
- safe provider metadata;
- report and raw Proof Bundle.

### Step 6: Demonstrate failure

From Mission Control or CLI, run artifact, event, and metadata tamper
cases. Each disposable copy must return `FAILED` with an exact reason.
The untouched original must still return `LOCAL_VERIFIED`.

This is the central demo moment because it gives meaning to the earlier
success badge.

### Step 7: Optional live provider

Only after the deterministic system is understood should the evaluator
consider a configured GPT-5.6 run. The live provider changes the
proposal source, not the trust model. The model still cannot approve
itself, and the receipt remains `UNANCHORED`.

### The ninety-second story

A short video can show:

1.  the mission contract;
2.  one fixture run;
3.  artifacts and passed checks;
4.  `LOCAL_VERIFIED` plus `UNANCHORED`;
5.  the event chain and Merkle root;
6.  an artifact tamper case returning `FAILED`;
7.  the original re-verifying successfully.

The longer five-minute path lets a judge reproduce all three tamper
classes and inspect the raw bundle.

### Why this path works

The demo is robust because it does not depend on a secret, internet
connection, model availability, or hidden state. Every central product
claim is visible through the same code paths used in tests and CLI
operation. The optional live integration is an extension, not a
theatrical dependency.

### Repository evidence

- `docs/BUILD_WEEK.md`
- `docs/DEMO_SCRIPT.md`
- `README.md`

## Chapter 28 — Product Differentiation

APR occupies a narrow layer between autonomous execution and human
trust. Its differentation comes from the combination of predeclared
authority, portable evidence, independent replay, and visible negative
cases.

### Not an agent framework

Agent frameworks help models plan, use tools, maintain state, and
coordinate. APR does not replace those capabilities. It can receive a
bounded mission from an agent system and return a receipt that survives
outside the framework.

This separation allows multiple agent runtimes to share evidence
semantics instead of forcing one orchestration library to become the
universal trust layer.

### More than observability

Observability platforms collect logs, traces, and metrics. APR records a
versioned contract, deterministic acceptance evidence, artifact digests,
a hash-linked event stream, a Merkle root, and a whole-bundle hash. The
independent verifier recomputes those values instead of searching logs
for a success statement.

APR can still export operational signals to observability tools. The
distinction is that proof-relevant evidence has canonical semantics.

### Not model self-evaluation

LLM-as-judge techniques are useful for subjective quality assessment,
but a model grading its own or another model’s output remains
probabilistic. APR assigns objective conditions to deterministic checks
and cryptographic consistency to a non-model verifier. Human judgment
remains available for everything those checks do not prove.

### Not blockchain by default

APR uses SHA-256 and a Merkle construction, but cryptographic data
structures do not make it a blockchain product. The current root is
local and unanchored. A future append-only service, public log, or chain
adapter could anchor bundle hashes, but the value of the receipt does
not depend on pretending that such an anchor already exists.

### Not a generic code-execution cloud

The Build Week runtime accepts controlled text proposals, not arbitrary
provider commands. The preserved gVisor adapter points toward stronger
isolated workloads, but general hostile-code execution is not smuggled
into the current claim.

### The combined advantage

The differentiated product loop is:

- contract before execution;
- model output as data, not authority;
- exact artifact permissions;
- deterministic objective acceptance;
- structured cryptographic receipt;
- verifier separate from stored runtime success;
- tamper detection users can observe;
- conservative labels for unsolved trust.

Many products implement one or two items. APR treats the whole loop as
one product. Its competitive strength is not a stronger adjective. It is
a more defensible answer to three questions: what was supposed to
happen, what evidence exists, and can another process check that
evidence?

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 28
- `docs/PROJECT_MANIFESTO.md`

# Part VIII — The Path Forward

## Chapter 29 — Roadmap

APR’s roadmap strengthens two different axes over time: execution
isolation and trust outside the runtime host. Neither should be confused
with adding more model features.

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

This phase proved that an execution receipt could be produced and
independently recomputed without a web interface or external service.

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

The repository records the fixture path, local/container judge flow,
hosted Mission Control, and one controlled live provider run as
validated within their stated boundaries.

### Phase 2 — Stronger execution boundary

The next isolation phase requires real runtime validation, not only
adapter code:

- a Linux Docker host with registered `runsc`;
- pinned and reproducible workload images;
- read-only base filesystem and controlled mounts;
- enforced egress policy;
- unprivileged execution;
- timeout, fork, resource-exhaustion, and escape regression tests;
- comparison of gVisor with a microVM backend where cost and startup
  latency justify it.

Success in this phase would justify a stronger execution security label.
It would not automatically change `UNANCHORED`.

### Phase 3 — Trust outside the runtime host

External trust requires another authority or preserved system boundary:

- signed receipts;
- append-only anchor service on a separate host;
- transparency log;
- inclusion proofs;
- independent timestamps;
- key rotation and revocation;
- key custody outside the runtime process.

Only this phase can support statuses such as `SIGNED_ONLY` or
`ANCHORED`, and only after their exact semantics and validation are
defined. A root submitted somewhere is not enough; clients must verify
signatures, log identity, inclusion, and freshness.

### Phase 4 — Interoperability

Once evidence semantics are stable, APR can map them into broader
ecosystems:

- published schema and canonicalization profiles;
- cross-language test vectors;
- independently implemented verifiers;
- in-toto-compatible statements and predicates;
- software supply-chain evidence adapters;
- portable policy packs;
- multiple runtime profiles sharing receipt semantics.

Interoperability is valuable because no single agent runtime should own
the only verifier of its receipts.

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

These requirements are not a natural consequence of adding a dashboard.
They are a different assurance level and must be designed, implemented,
tested, operated, and audited as such.

### Roadmap discipline

Every phase follows the same rule: code, tests, and observed validation
must precede stronger product claims. The roadmap is a direction, not
borrowed credibility.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 29
- `docs/ROADMAP.md`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 30 — Product Invariants

Features can evolve while the product’s core meaning remains stable. APR
defines ten invariants that any future architecture must preserve unless
an explicit, reviewable decision changes them.

### 1. The verifier does not trust stored runtime success

The runtime may record a claim, but verification must derive its own
result from the supported evidence. A UI badge or bundle field cannot
become the proof authority.

### 2. The model never determines cryptographic validity

A provider may create content, summarize, or explain. It may not decide
whether hashes, chains, roots, signatures, or inclusion proofs are
valid.

### 3. Provider output remains constrained by runtime policy

Structured output improves reliability but does not grant authority.
Paths, media types, counts, sizes, execution permissions, and side
effects remain under explicit runtime enforcement.

### 4. Evidence survives outside Mission Control

The portable receipt and verifier are primary. A user interface may
disappear, change, or be replaced without making historical evidence
meaningless.

### 5. Secrets and hidden reasoning never enter the Proof Bundle

Credentials, authorization headers, secret environment variables, raw
chain-of-thought, and uncontrolled internal traces are outside the
evidence contract. The absence of those values must be tested.

### 6. Local verification is never mislabeled as external anchoring

`LOCAL_VERIFIED` and `UNANCHORED` answer different questions. A local
bundle hash, Merkle root, hosted URL, or successful API call does not
create non-repudiation.

### 7. Unsupported isolation is never claimed as active

An implementation path, Dockerfile, or simulated test is not a real
gVisor or microVM validation. Backends must fail closed and report
actual detection state.

### 8. Tamper demonstrations never modify the original run

Security demonstration uses a disposable copy and verifies original
fingerprints before and after. Evidence evaluation must not destroy its
source.

### 9. New bundle versions do not silently invalidate old receipts

Verification dispatches by schema version. New semantics require a new
version, clear rejection of unsupported formats, compatibility tests,
and migration guidance where appropriate.

### 10. Human approval remains separate from technical verification

Integrity evidence informs a decision. It does not determine strategic
value, ethics, legal sufficiency, customer acceptance, or deployment
authority.

### Invariants as a review tool

These rules turn architectural review into concrete questions. Does a
new provider receive arbitrary command execution? Does a hosted redesign
hide `UNANCHORED`? Does a bundle extension persist raw model traces?
Does a performance optimization stop reproducing acceptance? Does a new
UI invent a success state? Does a migration drop v0.1 verification?

If the answer threatens an invariant, the change needs an explicit
architecture decision and evidence. Speed is not a reason to make the
trust model implicit.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 30
- `docs/PROJECT_MANIFESTO.md` section 13

## Chapter 31 — Definition of Done: Build Week v0.2

A vertical slice is done when the complete operator story works and its
negative claims remain honest. APR’s Definition of Done combines
compatibility, functionality, security regression, documentation, and
validation.

### Contract and provider

- A versioned safe mission loads under strict validation.
- Fixture mode completes without a secret or network call.
- The optional OpenAI provider implements the same proposal boundary.
- Structured output cannot grant arbitrary host commands or paths.
- Provider absence and missing credentials fail clearly.

### Runtime and acceptance

- Proposed artifacts are materialized only after exact policy
  enforcement.
- Required files, media types, duplicate paths, counts, and byte limits
  are enforced.
- Deterministic acceptance evidence is recorded.
- Mission failure remains distinct from proof failure.

### Receipt and verification

- A versioned Proof Bundle is produced.
- The independent verifier returns `LOCAL_VERIFIED` for untouched valid
  evidence.
- Artifact modification returns `FAILED`.
- Event modification returns `FAILED`.
- Critical metadata modification returns `FAILED`.
- The original run remains unchanged after every Tamper Lab case.
- v0.1 and v0.2 receipts retain their verification semantics.

### Operator surfaces

- The CLI exposes validation, execution, verification, tampering,
  diagnostics, and Mission Control startup.
- Mission Control exposes the complete judge path.
- The interface maps statuses to evidence and shows trust boundaries.
- `/health` succeeds.
- HTTP controls cover Host validation, CSRF, CSP, paths, traversal, and
  symlinks.

### Repository and operations

- The legacy suite remains green on supported Python versions.
- CI executes the fixture path without a live API call.
- Generated runs and secrets are not tracked.
- Baseline, collaboration, architecture, deployment, and validation
  records exist.
- The Build Week branch preserves implementation lineage.
- Deployment limitations are stated honestly.

### Recorded completion state

The repository’s gap audit marks the competition-critical fixture
vertical slice as complete and independently verifiable. It records the
OpenAI provider as delivered and live-validated in one controlled local
run. It records the Docker image and public Mission Control judge flow
as validated. It also leaves two major boundaries open by design:

- real Linux Docker + `runsc` validation for hardened gVisor execution;
- external signing or append-only anchoring for non-repudiation.

Those open items do not make the delivered vertical slice incomplete.
They prevent the current product from claiming a stronger assurance
level.

Definition of Done is therefore not “everything on the roadmap exists.”
It is “the locked slice works end to end, failures are observable, tests
protect the contract, and every limitation is labeled accurately.”

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 31
- `docs/BUILD_WEEK_GAP_AUDIT.md`
- `docs/LIVE_VALIDATION.md`
- `docs/HOSTED_VALIDATION.md`

## Chapter 32 — Final Product Statement

Autonomous systems will increasingly act before a human reviews every
individual step. That transition cannot rest on screenshots, confidence
scores, and self-reported success.

An agent can say that it completed a task. It can produce a polished
artifact. It can narrate a plausible execution. None of those things
independently establishes what contract governed the run, what authority
the provider held, which bytes were materialized, which objective checks
actually passed, or whether the evidence changed afterward.

Agent Proof Runtime begins by making the contract explicit.

The Mission Manifest states what should happen, what the provider may
produce, how large the output may become, and which objective conditions
will be evaluated. The provider proposes structured artifacts but cannot
expand its own authority. The runtime enforces paths, media types,
counts, and byte limits before creating files. The acceptance engine
evaluates bounded deterministic predicates without asking the model to
grade itself.

The runtime then leaves a receipt. Events are canonicalized, hashed, and
linked. Artifact bytes receive digests. Event hashes form a
domain-separated Merkle tree. The mission, provider metadata, artifacts,
acceptance evidence, events, and trust labels become a versioned Proof
Bundle with a recomputable whole-document hash.

Another process opens that receipt and starts again. It does not accept
the stored success label. It resolves paths safely, reads the artifacts,
rebuilds hashes and links, reproduces acceptance, and derives its own
result. Mission Control explains the evidence, but it is not the
evidence. Tamper Lab changes a disposable copy so the user can watch
verification fail while the original remains intact.

The result is not omniscience.

APR does not prove that an agent chose the best strategy. It does not
turn a passed file check into semantic truth. It does not call a local
hash an external signature. It does not call an ordinary process a
secure sandbox. It does not replace the human who must decide whether an
output is useful, ethical, legal, or ready to deploy.

Those limits are part of the product, not footnotes to hide.

The current system proves a narrower and more practical proposition:
autonomous work can be placed under an explicit contract, constrained to
a declared artifact surface, recorded as structured evidence, and
checked independently for local integrity. That foundation can later
gain stronger isolation, external signatures, append-only anchoring,
interoperability, and regulated profiles without abandoning the
semantics of the original receipt.

The product doctrine fits into four lines:

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.

Agent Proof Runtime does not ask users to trust autonomous execution
because a model sounds certain.

It gives them a contract, a receipt, and an independent method of
checking the evidence.

That is the beginning of accountable autonomy.

That is proof before trust.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md` section 16
- `docs/PRODUCT_BLUEPRINT.md` section 32
