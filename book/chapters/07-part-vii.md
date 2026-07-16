# Part VII — Evaluation and Differentiation

## Chapter 25 — Failure Model

APR treats failure as a structured outcome rather than a single exception class.
The stage at which a mission fails determines what evidence exists, which component
needs attention, and whether a Proof Bundle can still be valid.

### Manifest failure

The requested mission violates schema or policy before provider execution. Examples
include unknown fields, duplicate JSON keys, unsafe paths, unsupported media types,
invalid limits, malformed checks, or an unsupported schema version.

The remedy belongs to the Mission Author. The provider should not be called because
the contract is not valid enough to grant authority.

### Provider failure

The provider is unavailable, misconfigured, unauthorized, timed out, missing its
optional dependency, or returned malformed structured output. The mission itself
may be valid, but no acceptable proposal exists.

APR reports this domain explicitly. A requested OpenAI execution must not pretend to
succeed through a fixture fallback, because that would change the declared
experiment.

### Policy failure

The proposal is structurally valid but violates the artifact contract. It may
contain an undeclared path, duplicate target, wrong media type, missing required
file, too many files, or excessive bytes. This is neither a transport error nor an
acceptance failure. The runtime refused authority before materialization.

### Acceptance failure

The runtime safely materialized permitted artifacts, but one or more declared
objective checks did not pass. The mission outcome is `FAILED`.

This failure can still produce a `LOCAL_VERIFIED` proof. The verifier confirms that
the failed checks, artifacts, events, and hashes were recorded consistently. A
faithful receipt of failure is often more valuable than a success message without
evidence.

### Verification failure

The evidence is missing, malformed, unsafe, inconsistent, unsupported, or modified.
Examples include an artifact digest mismatch, missing file, symlink, broken event
link, wrong Merkle root, changed acceptance record, incorrect bundle hash, or
unsupported schema. The proof result is `FAILED`, regardless of how useful the
artifact appears.

Verification failure should stop downstream trust decisions. It does not
automatically reveal whether the cause was malicious tampering, accidental
corruption, incomplete copying, or a software defect. It establishes that the
available evidence cannot support the claimed consistency.

### Operational failure

The server cannot bind, the output directory already exists, the filesystem is
unavailable, a container cannot start, the required backend is missing, or another
environmental condition blocks execution. These failures belong to operation rather
than mission semantics.

### A failure matrix

| Domain | Contract valid? | Artifacts may exist? | Acceptance meaningful? | Proof may be valid? |
|---|---:|---:|---:|---:|
| Manifest | No | No | No | Usually no run bundle |
| Provider | Yes | Usually no | No | Failure evidence may be recorded in future profiles |
| Policy | Yes | No committed run in v1 path | No | No completed v1 bundle |
| Acceptance | Yes | Yes | Yes, failed | Yes, `LOCAL_VERIFIED` possible |
| Verification | Unknown or changed | Maybe | Maybe | No, `FAILED` |
| Operational | Maybe | Maybe partial | Maybe | Depends on completed evidence |

Precise failure semantics prevent unsafe recovery. Retrying a provider timeout may
be appropriate. Retrying an unsafe path without changing the contract is not.
Deploying an acceptance-failed artifact requires a human decision. Ignoring a
verification failure defeats the product.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 25
- `src/agent_proof_runtime/cli.py`
- `src/agent_proof_runtime/validator.py`

## Chapter 26 — Product Metrics

Early APR success is not measured by user growth or the number of integrations. It
is measured by whether the core evidence loop is understandable, reproducible, and
honest.

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

The secret metric is absolute. An average close to zero is not acceptable for API
keys. Tests should use sentinel values and scan all persisted outputs. Controlled
live validation should remove process environment values immediately after the run
and record only that the scan passed, never the secret itself.

### Performance metrics

For the deterministic path, median mission duration and independent verification
duration help detect regressions. Time to first verified run is more useful than raw
throughput during evaluation. A judge should not wait through infrastructure that
does not contribute to understanding.

Performance should not be optimized by weakening checks. If a bundle verifies
faster because acceptance reproduction or artifact scanning was removed, the metric
has become detached from product value.

### Usability metrics

APR's Build Week product has a concrete comprehension goal:

> Can a new evaluator execute, inspect, verify, tamper, and re-verify the complete
> flow within five minutes?

Additional useful observations include:

- whether the evaluator can explain the difference between mission and proof status;
- whether `UNANCHORED` is visible without reading source code;
- whether a tamper failure names the modified layer;
- whether the raw bundle can be located and verified outside the UI;
- whether the fixture path works without configuration.

These are not vanity metrics. They test whether the trust model survives contact
with a real operator.

### Security-claim metrics

Claim discipline can itself be evaluated. Every present-tense security label should
map to code and validation. Every roadmap capability should be marked as such. A
deployment should report its storage and authentication limits. A backend should
not be called gVisor-validated without a real `runsc` run.

One useful governance metric is the number of claims that exceed evidence. The
target is zero.

### Metrics after external anchoring

Future phases may add anchor submission success, inclusion-proof verification,
signature validation, key rotation coverage, timestamp latency, revocation behavior,
and independent verifier interoperability. Those metrics should appear only when the
corresponding mechanisms exist.

APR begins by measuring the behavior it can actually reproduce. That is consistent
with the product's central doctrine: evidence before confidence.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 26
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 27 — Build Week Judge Path

The judge path compresses the product into one reproducible story. Its purpose is
not to hide complexity. It is to reveal the central contract, evidence, and failure
behavior before an evaluator chooses to inspect deeper layers.

### Step 1: Start from a deterministic environment

Install the package in Python 3.11 or 3.12 without the optional model SDK:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Step 2: Validate the mission

```bash
apr mission validate examples/build-week-mission.json
```

The operator sees that the contract is accepted before execution. The checked-in
mission is safe, finite, and requires no secret.

### Step 3: Run the fixture path

```bash
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/judge-demo
```

The fixture traverses the same proposal, policy, materialization, acceptance, event,
bundle, verification, and report path used by the live adapter.

### Step 4: Verify outside the UI

```bash
apr verify .runs/judge-demo/proof-bundle.json
```

Expected labels:

```text
Mission: PASSED
Proof:   LOCAL_VERIFIED
Anchor:  UNANCHORED
```

This establishes that Mission Control will visualize an independently verified
receipt rather than inventing the result.

### Step 5: Open Mission Control

```bash
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

From Mission Control or CLI, run artifact, event, and metadata tamper cases. Each
disposable copy must return `FAILED` with an exact reason. The untouched original
must still return `LOCAL_VERIFIED`.

This is the central demo moment because it gives meaning to the earlier success
badge.

### Step 7: Optional live provider

Only after the deterministic system is understood should the evaluator consider a
configured GPT-5.6 run. The live provider changes the proposal source, not the trust
model. The model still cannot approve itself, and the receipt remains
`UNANCHORED`.

### The ninety-second story

A short video can show:

1. the mission contract;
2. one fixture run;
3. artifacts and passed checks;
4. `LOCAL_VERIFIED` plus `UNANCHORED`;
5. the event chain and Merkle root;
6. an artifact tamper case returning `FAILED`;
7. the original re-verifying successfully.

The longer five-minute path lets a judge reproduce all three tamper classes and
inspect the raw bundle.

### Why this path works

The demo is robust because it does not depend on a secret, internet connection,
model availability, or hidden state. Every central product claim is visible through
the same code paths used in tests and CLI operation. The optional live integration
is an extension, not a theatrical dependency.

### Repository evidence

- `docs/BUILD_WEEK.md`
- `docs/DEMO_SCRIPT.md`
- `README.md`

## Chapter 28 — Product Differentiation

APR occupies a narrow layer between autonomous execution and human trust. Its
differentation comes from the combination of predeclared authority, portable
evidence, independent replay, and visible negative cases.

### Not an agent framework

Agent frameworks help models plan, use tools, maintain state, and coordinate. APR
does not replace those capabilities. It can receive a bounded mission from an agent
system and return a receipt that survives outside the framework.

This separation allows multiple agent runtimes to share evidence semantics instead
of forcing one orchestration library to become the universal trust layer.

### More than observability

Observability platforms collect logs, traces, and metrics. APR records a versioned
contract, deterministic acceptance evidence, artifact digests, a hash-linked event
stream, a Merkle root, and a whole-bundle hash. The independent verifier recomputes
those values instead of searching logs for a success statement.

APR can still export operational signals to observability tools. The distinction is
that proof-relevant evidence has canonical semantics.

### Not model self-evaluation

LLM-as-judge techniques are useful for subjective quality assessment, but a model
grading its own or another model's output remains probabilistic. APR assigns
objective conditions to deterministic checks and cryptographic consistency to a
non-model verifier. Human judgment remains available for everything those checks do
not prove.

### Not blockchain by default

APR uses SHA-256 and a Merkle construction, but cryptographic data structures do not
make it a blockchain product. The current root is local and unanchored. A future
append-only service, public log, or chain adapter could anchor bundle hashes, but the
value of the receipt does not depend on pretending that such an anchor already
exists.

### Not a generic code-execution cloud

The Build Week runtime accepts controlled text proposals, not arbitrary provider
commands. The preserved gVisor adapter points toward stronger isolated workloads,
but general hostile-code execution is not smuggled into the current claim.

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

Many products implement one or two items. APR treats the whole loop as one product.
Its competitive strength is not a stronger adjective. It is a more defensible
answer to three questions: what was supposed to happen, what evidence exists, and
can another process check that evidence?

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 28
- `docs/PROJECT_MANIFESTO.md`
