# Preface

## Why this book exists

Autonomous AI systems are crossing a line. They no longer only answer questions.
They create files, modify repositories, call tools, run workflows, and prepare
actions that may affect customers, infrastructure, money, or public systems. The
industry has become very good at making these systems look capable. It is much less
mature at showing what actually happened after an autonomous task ends.

Most agent products present one of three things: a polished final answer, an
activity feed, or a confidence score. All three can be useful. None is independent
proof. A final answer can omit failed steps. An activity feed can be incomplete or
changed. A confidence score is still a claim made by the system being evaluated.

Agent Proof Runtime began with a deliberately narrower question:

> Can an agent mission leave behind a portable execution receipt that another
> process can verify without trusting the agent, the runtime's stored success
> label, or the user interface?

That question leads to a different product architecture. The mission must be
declared before execution. Model output must be treated as untrusted data. The
runtime must enforce explicit authority over paths, file types, counts, and sizes.
Objective acceptance conditions should be deterministic. Important events and
artifacts should be bound to cryptographic digests. A separate verifier should
derive its own result. The final operator should see both the evidence and the
limits of that evidence.

This book explains that architecture as a product and as an engineering method. It
is not a theoretical security proof and not a claim that APR solves every problem
in agent safety. It describes the system that exists in the repository, the
boundaries the project states openly, and the path from a local proof slice toward
stronger external trust.

## A book built from a repository

The factual hierarchy for this manuscript is explicit:

1. implementation and tests,
2. locked architecture documents,
3. validation records,
4. product doctrine and roadmap,
5. this narrative explanation.

If prose and implementation disagree, the implementation and its reproducible
tests win. If two documents describe different moments in time, the later
validation record governs the current claim while the older document remains
useful provenance. The manuscript therefore separates four kinds of statement:

- **Implemented:** code exists in the active product branch.
- **Tested:** an automated or controlled validation covers the behavior.
- **Observed:** a dated validation record reports a real run or deployment.
- **Roadmap:** the capability is intended but must not be presented as delivered.

This matters because systems about trust lose credibility the moment their own
claims outrun their evidence.

## The central distinction

APR does not try to prove that an AI made the best decision. That claim is too broad
for the evidence the runtime can currently produce. APR makes narrower claims that
can be checked:

- a particular mission contract was recorded;
- a provider returned a structured proposal;
- only declared artifacts were materialized;
- deterministic checks produced recorded results;
- files still match their recorded hashes;
- events form the expected hash chain;
- the Merkle root and whole-bundle hash can be recomputed;
- protected changes become detectable within the local trust boundary.

Those claims are useful precisely because they are limited. `LOCAL_VERIFIED` means
internal evidence is consistent. It does not mean the run is externally signed,
remotely anchored, semantically perfect, or safe against a fully privileged host
administrator who replaces the evidence and recomputes it. APR uses `UNANCHORED`
and `development-only` to keep those limits visible.

## The operating doctrine

The complete product can be summarized in four sentences:

> The agent performs the work.  
> The runtime records the evidence.  
> The verifier checks the proof.  
> The human makes the decision.

Each sentence assigns authority to a different component. The provider is allowed
to propose artifacts, not to authorize itself. The runtime is allowed to enforce
policy and build evidence, not to be the sole judge of that evidence. The verifier
is allowed to calculate integrity, not to decide whether a business outcome is
desirable. The human remains responsible for approval, deployment, and consequence.

That separation is the recurring pattern throughout the next thirty-two chapters.

## How to use this book

Readers building agent infrastructure can treat the book as an architectural
walkthrough. Security reviewers can focus on Parts II, IV, V, and VI. Product
operators can begin with Parts I, VII, and VIII. A judge or evaluator can follow the
five-minute path in Chapter 27 and then return to the underlying contracts.

The examples intentionally favor a deterministic fixture. A useful verification
product cannot require a third-party model, a network call, or a secret merely to
demonstrate its core correctness. APR's optional OpenAI provider traverses the same
proposal, policy, acceptance, event, bundle, and verification contracts, but it is
not the root of trust.

The project begins with proof before trust. The book begins at the same place: not
with a promise that autonomous agents are reliable, but with a method for making
their execution claims inspectable.

### Repository evidence

- `docs/PROJECT_MANIFESTO.md`
- `docs/PRODUCT_BLUEPRINT.md`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md`
- `docs/LIVE_VALIDATION.md`
- `docs/HOSTED_VALIDATION.md`
