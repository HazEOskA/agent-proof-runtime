# Part I — The Trust Gap and the Product

## Chapter 1 — Executive Summary

An autonomous agent can create a convincing result while leaving the operator
unable to answer basic questions about the execution. Which mission did it really
follow? Which provider response influenced the output? Which files were permitted?
Which checks ran? Did the evidence change after completion? Can anybody other than
the system that performed the work verify its claims?

Agent Proof Runtime is an execution-evidence layer designed around those questions.
Its purpose is not to make an agent intelligent and not to replace an agent
framework. APR sits around an autonomous task and turns a declared mission into a
portable receipt of execution.

The Build Week path is intentionally narrow:

```text
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

The flow begins with a contract rather than a prompt. A versioned Mission Manifest
declares the goal, provider, model, exact artifact surface, resource limits,
acceptance checks, and reasoning-retention policy. Unknown fields, duplicate JSON
keys, absolute paths, traversal segments, unsupported media types, malformed checks,
and invalid limits are rejected before execution.

The selected provider has a deliberately small job: return a structured artifact
proposal. In deterministic mode, a fixture produces repeatable output without a
network or secret. In optional live mode, the OpenAI adapter requests strict
Structured Output from GPT-5.6. Both return the same conceptual object. Neither is
granted authority to run shell commands, choose arbitrary filesystem paths, or
declare its own proof valid.

The runtime then applies policy that exists outside the model. It checks exact path
membership, media types, required files, duplicate paths, per-file and total byte
limits, and file-count limits. It creates a fresh destination and writes permitted
text artifacts with exclusive creation semantics. The system re-reads the files,
calculates digests, and evaluates six allowlisted deterministic check types:
`file_exists`, `file_count`, `contains_text`, `json_valid`,
`json_required_keys`, and `maximum_size`.

During execution, significant transitions become canonical events. Each event is
bound to the previous event through SHA-256. Event hashes become leaves in an RFC
6962-style Merkle construction. The final Proof Bundle contains the canonical
mission, provider metadata safe for persistence, artifact records, acceptance
evidence, events, integrity roots, runtime claim, and anchor status.

The important step comes afterward. A separate verifier opens the bundle and does
not trust the stored success label. It validates the schema, resolves artifact paths
safely, rejects symlinks and traversal, re-hashes files, rebuilds the event chain,
recomputes the Merkle root and whole-bundle hash, reproduces acceptance checks, and
cross-checks critical metadata. Its result is derived from evidence.

This produces a small but meaningful trust vocabulary:

| Label | Meaning |
|---|---|
| `LOCAL_VERIFIED` | The independent verifier found the bundle and referenced artifacts internally consistent within the local trust boundary. |
| `FAILED` | At least one required schema, path, artifact, event, acceptance, or integrity condition did not hold. |
| `UNANCHORED` | No independent external log, signature service, or hardware-backed authority vouched for the bundle. |
| `development-only` | The controlled-artifact/local process path is not presented as hostile-code isolation. |

These labels prevent a common category error. Mission success and proof validity are
not the same thing. A mission may legitimately fail its acceptance criteria while
the proof remains `LOCAL_VERIFIED`, because the verifier confirms that the failure
was recorded consistently. Conversely, an artifact may look useful while its proof
is `FAILED`, because the evidence was altered or became inconsistent.

Mission Control makes this flow visible. It allows an operator to select a checked-
in mission, run it through the fixture or configured live provider, inspect
artifacts, view checks and events, see the Merkle root and bundle hash, and request
independent re-verification. The interface is an adapter over the same runner and
verifier used by the CLI; it is not an alternative source of truth.

Tamper Lab completes the demonstration. It copies a verified run, changes one
artifact, event, or critical metadata field, runs the verifier against the copy,
reports the exact failure, deletes the disposable copy, and confirms the original
run's fingerprint remains unchanged. The product does not merely say that tampering
is detectable. It lets the user observe detection.

The current result is useful but deliberately bounded. The fixture path, verifier,
Mission Control, Tamper Lab, Docker deployment, hosted judge flow, and one controlled
GPT-5.6 provider run have validation records in the repository. External anchoring,
out-of-host signing, hostile-code isolation in the controlled-artifact path,
multi-tenant authentication, HSM/TEE guarantees, and real gVisor execution remain
outside the delivered trust boundary.

APR therefore makes a precise promise: it converts autonomous agent activity into
independently verifiable execution evidence. It does not ask the evidence to prove
more than it can.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` sections 1 and 5
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 2 — Product Definition

Agent Proof Runtime is best understood by separating it from adjacent product
categories. It is not primarily a chat interface, an agent framework, a model
router, a generic observability dashboard, a blockchain product, or a full code-
execution cloud. Those products may become sources or consumers of APR evidence,
but none defines its central role.

The one-sentence definition is:

> Agent Proof Runtime converts autonomous agent activity into independently
> verifiable execution evidence.

Three words in that sentence carry most of the architecture.

**Execution** means APR cares about the path between intention and output, not only
the final content. A useful artifact without a declared mission, event record, or
acceptance evidence may still be useful, but it is not a complete APR result.

**Evidence** means the product records inspectable facts: normalized contracts,
provider metadata, artifact bytes and hashes, deterministic observations, ordered
events, and integrity roots. Evidence is different from an explanation. An agent
may explain what it believes happened. APR records material that can be checked.

**Independently verifiable** means the process that produced the evidence is not the
only authority deciding whether that evidence is internally consistent. The
verifier may share canonicalization and deterministic evaluation functions because
identical rules must be reproducible, but it does not trust the runtime's final
status. It derives a verdict from the bundle and files it reads.

The product promise can then be expressed as a concrete handoff. A user submits a
versioned mission and receives:

- materialized artifacts;
- a structured event timeline;
- deterministic acceptance results;
- cryptographic integrity metadata;
- a portable Proof Bundle;
- an independently derived verification result.

This is narrower than promising that the agent was correct. APR does not determine
whether a design is beautiful, a business decision is wise, a legal analysis is
complete, or generated code is free of every vulnerability. It can prove that a
declared file existed, contained required text, formed valid JSON, included required
keys, remained below a size limit, and still matches its recorded digest. It can
prove that the evidence structure recomputes. It cannot turn those objective facts
into universal semantic truth.

The primary user journey reflects this restraint:

1. Select a safe, declared mission.
2. Run it with a deterministic fixture or configured live provider.
3. Inspect the generated artifacts.
4. Review objective acceptance checks.
5. Examine the event timeline and integrity values.
6. Invoke independent verification.
7. Create a disposable tampered copy.
8. Observe verification fail for a precise reason.

That final contrast matters. Trust mechanisms often remain abstract until failure
is visible. The difference between the untouched `LOCAL_VERIFIED` run and a modified
`FAILED` copy gives operators a working mental model of what APR protects.

The product also creates a useful interface boundary for agent builders. Providers
do not need to understand hash chains or the bundle schema. They need to return a
valid proposal. Agent frameworks do not need to become cryptographic verifiers.
They can submit bounded work and consume a receipt. Mission Control does not need to
reimplement integrity logic. It calls the same verifier. Each component has a
smaller responsibility than a monolithic "trusted agent" would require.

APR is therefore both a product and an architectural position. Autonomous systems
should not earn trust by narrating their own success. They should operate under an
explicit contract, leave portable evidence, and accept an independent check.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md` sections 3–5
- `docs/PRODUCT_BLUEPRINT.md` sections 2 and 4

## Chapter 3 — Target Users

The first APR users are not people looking for another general-purpose chatbot.
They are builders and reviewers who already understand that autonomous execution
creates an operational gap.

### Developers of autonomous agents

Agent developers need to debug more than a final response. They need to know which
contract reached the runtime, what structured output arrived, what policy rejected,
which files were accepted, and which deterministic conditions held. A Proof Bundle
turns those facts into a stable artifact that survives beyond terminal output.

For a coding agent, this could mean declaring an exact patch artifact, expected file
count, byte ceiling, and machine-checkable properties before the model is invoked.
APR does not yet claim safe arbitrary code execution in the Build Week path, but the
contract-and-receipt pattern applies directly to stronger future backends.

### Agentic workflow engineers

Workflow builders often connect probabilistic decisions to deterministic tools.
Their systems may succeed for weeks and then fail in a way that is difficult to
reconstruct. APR offers a neutral boundary between a provider's proposal and the
side effects permitted by a runtime. The workflow can carry a bundle hash and run
identifier into later stages instead of relying on a mutable activity log.

### AI infrastructure and QA teams

Infrastructure teams care about reproducibility, versioning, and compatibility.
APR's fixture-first path is valuable because it separates runtime correctness from
provider availability. The same mission can traverse proposal parsing, policy,
materialization, acceptance, event creation, bundle generation, and verification in
CI without a key or external request.

AI QA teams can use the failure vocabulary to distinguish categories that generic
test dashboards often collapse: invalid manifest, provider failure, policy failure,
acceptance failure, verification failure, and operational failure. A precise
failure domain is the beginning of useful remediation.

### Security-conscious automation teams

Security reviewers are natural users because APR makes its trust boundary explicit.
They can inspect which fields are canonicalized, how paths are resolved, whether
symlinks are rejected, how event linkage works, and what the verifier recomputes.
They can also see what remains unsolved. A local unsigned bundle is not presented as
non-repudiation. A Docker image is not automatically called a hostile-code sandbox.

### Technical auditors and judges

An auditor should not need to understand every source file before evaluating a
small claim. APR provides a short path from mission to artifact to receipt to
verification to deliberate failure. The Proof Bundle remains available for deeper
inspection, while Mission Control makes the evidence legible.

### Future regulated operators

Financial, healthcare, public-sector, and compliance teams are plausible later
users, but their presence on the roadmap must not inflate current claims. They may
require signed receipts, trusted timestamps, external append-only logs, durable
retention, identity, role-based access, PII controls, hardware-backed keys, and
independent audits. The local Build Week profile is a foundation, not a regulatory
certificate.

The common trait across these groups is not industry. It is the need to separate an
autonomous system's assertion from independently checkable evidence.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 3
- `docs/ROADMAP.md`

## Chapter 4 — User Roles

Reliable agent systems become easier to reason about when responsibility is divided
by role. APR defines six conceptual roles. A small installation may place several
roles in one person or process, but their authority should still remain distinct.

### The Mission Author

The Mission Author decides what the task means before execution. This role defines
the goal, provider policy, model request, exact artifact contract, limits,
deterministic acceptance checks, and analysis-retention policy.

The author is powerful because an incorrect contract can make a run useless while
remaining perfectly verifiable. If the manifest checks only that `report.json`
exists, APR can prove existence but not whether the report contains the business
analysis the operator needed. Good verification begins with a good contract.

The author cannot control the verifier's result. Changing the manifest after a run
changes its canonical hash and should invalidate the relationship to the recorded
evidence.

### The Operator

The Operator starts missions, inspects artifacts, reviews checks, invokes
verification, and decides what to do with the result. The operator may accept,
reject, revise, or stop a downstream action. APR provides evidence; it does not
seize this authority.

This distinction is crucial in real workflows. `LOCAL_VERIFIED` is not an automatic
deployment approval. It says that the available evidence is internally consistent.
The operator may still reject the artifact for quality, ethics, strategy, or risk.

### The Provider

The Provider proposes structured artifacts. It may be the deterministic fixture,
GPT-5.6 through the optional OpenAI adapter, or a future compatible integration.
The provider is not allowed to write arbitrary host files, choose shell commands,
expand the manifest, waive byte limits, or declare cryptographic validity.

Treating the provider as untrusted input is not an insult to the model. It is a
sound systems boundary. Powerful components should receive only the authority
required for their task.

### The Runtime

The Runtime validates the mission, invokes the selected provider, parses the
proposal, enforces policy, materializes permitted artifacts, runs deterministic
checks, records events, and builds the Proof Bundle. It is the execution coordinator
and evidence producer.

The runtime does write a claimed status into the bundle because operational state
must be recorded. That claim is evidence input, not the final verdict.

### The Independent Verifier

The verifier reads the bundle and artifacts after execution. It validates supported
schema versions, checks paths, re-hashes files, rebuilds chains and roots, reproduces
acceptance evidence, cross-checks metadata, and emits its own result. It does not ask
the provider whether the run was valid and does not trust Mission Control's badge.

Independence here is logical and procedural, not yet external-host independence.
The verifier can run as a separate command and on copied evidence, but a privileged
attacker who owns the host may still replace both evidence and verifier. External
trust is a later phase.

### The Judge or Auditor

The Judge or Auditor evaluates the product through a controlled path. This role
starts with a checked-in fixture mission, observes a verified result, changes a
disposable copy in Tamper Lab, and confirms that failure is detected while the
original remains intact. The role is deliberately given a reproducible path rather
than a promotional demo that depends on hidden setup.

Together, these roles define APR's authority model:

| Role | May do | Must not be treated as |
|---|---|---|
| Mission Author | Declare contract | Proof authority |
| Operator | Decide and approve | Cryptographic calculator |
| Provider | Propose artifacts | Host administrator or verifier |
| Runtime | Enforce and record | Sole judge of its own evidence |
| Verifier | Recompute integrity | Business approver |
| Judge/Auditor | Evaluate claims | Hidden privileged operator |

The separation prevents one component from becoming author, executor, witness,
judge, and approver at the same time.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 4
- `docs/PROJECT_MANIFESTO.md` sections 5, 6, and 12
