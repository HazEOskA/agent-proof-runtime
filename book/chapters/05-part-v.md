# Part V — Making Failure Visible

## Chapter 17 — Tamper Lab

Integrity systems are easiest to understand when users can watch them fail. Tamper
Lab turns APR's abstract protection claims into a controlled experiment.

The lab begins with an existing run and its Proof Bundle. It fingerprints every file
in the original run, creates a temporary copy, applies one supported mutation to the
copy, invokes the same independent verifier used elsewhere, captures the exact
failure reasons, and deletes the copy. It then fingerprints the original again and
confirms that the source evidence did not change.

The current lab supports three cases:

1. **Artifact tampering** changes materialized file content.
2. **Event tampering** changes protected event data.
3. **Metadata tampering** changes critical bundle metadata.

Each case targets a different integrity layer.

### Artifact tampering

When artifact bytes change, the recorded size or SHA-256 no longer matches. The
verifier re-reads the file and reports the discrepancy. Depending on the artifact,
the reproduced acceptance evidence may also change. The event record and bundle hash
still bind the original values, creating multiple observable inconsistencies.

### Event tampering

Changing an event's input, output, details, or type changes its canonical section
hash or step hash. Later predecessor linkage breaks, and the Merkle root no longer
matches the recomputed leaf set. The verifier reports the concrete chain and
integrity failures rather than assuming the stored hashes are authoritative.

### Metadata tampering

Critical metadata may sit outside artifact bytes and event content. Changing a
manifest value, provider field, run property, acceptance record, anchor label,
event count, Merkle root, or bundle-level field should be caught by schema,
cross-field, or whole-bundle checks. This case demonstrates why a bundle hash is
needed in addition to artifact hashes.

### Copy-on-tamper is a safety rule

The lab never modifies the original evidence. This is not merely convenient for a
demo. Security testing must not destroy the object it is supposed to evaluate. The
before-and-after fingerprint makes original preservation itself observable.

CLI examples are direct:

```bash
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case artifact
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case event
apr tamper-lab .runs/build-week-demo/proof-bundle.json --case metadata
```

The expected contrast is:

```text
Original run: LOCAL_VERIFIED
Tampered copy: FAILED
```

Tamper Lab does not prove resistance to a fully privileged attacker who replaces
the entire local system and recomputes every value. It proves that supported
modifications become visible to the independent verifier when evaluated against the
preserved receipt and rules.

The product lesson extends beyond APR: if a verification mechanism cannot
demonstrate a controlled negative case, users have little basis for understanding
what its positive result means.

### Repository evidence

- `src/agent_proof_runtime/tamper_lab.py`
- `tests/test_build_week_runtime.py`
- `docs/PRODUCT_BLUEPRINT.md` section 17

## Chapter 18 — CLI Product Surface

APR's command-line interface is the transparent automation surface beneath Mission
Control. It supports direct execution, independent verification, tamper experiments,
backend diagnostics, and legacy compatibility.

### Fixture-first judge path

A fresh Python 3.11 or 3.12 environment can run the complete deterministic flow:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

apr mission validate examples/build-week-mission.json
apr run examples/build-week-mission.json \
  --provider fixture \
  --output .runs/build-week-demo
apr verify .runs/build-week-demo/proof-bundle.json
```

The expected result is a mission `PASSED`, proof `LOCAL_VERIFIED`, and anchor
`UNANCHORED`. No key, network call, or optional SDK is required.

### Optional live provider

The live adapter is installed separately:

```bash
python -m pip install -e '.[openai]'
```

When `OPENAI_API_KEY` is already configured in the process environment, the same
mission can select the OpenAI provider:

```bash
APR_OPENAI_MODEL=gpt-5.6 apr run examples/build-week-mission.json \
  --provider openai \
  --output .runs/gpt-5-6-smoke
```

Missing credentials fail clearly. APR does not create, request, print, store, or
silently replace the key. A requested OpenAI run does not fall back to fixture mode.

### Independent verification

`apr verify` accepts a bundle path and produces an exit status suitable for scripts.
The verifier is version-aware, so legacy v0.1 and v0.2 receipts remain valid under
their own semantics while v1 uses the Build Week path.

### Legacy compatibility

The original proof slice remains available:

```bash
apr demo --output .runs/legacy-demo
apr verify .runs/legacy-demo/proof-bundle.json
```

MissionSpec v0.2 and its execution path also remain preserved. Backward
compatibility is a product invariant, not an incidental test.

### Mission Control and diagnostics

The interface starts with:

```bash
apr mission-control
```

`PORT` is honored, and host/port options can be passed explicitly. Binding beyond
loopback requires deliberate remote opt-in because the service does not claim
multi-user authentication.

Backend diagnosis is separate from execution:

```bash
apr doctor --backend gvisor
```

On a machine without Docker and registered `runsc`, the correct result is
unavailable. The command must not substitute `runc` and report a false gVisor
success.

### Exit codes as an API

A CLI is not reliable automation if every failure looks the same. APR distinguishes
successful execution from invalid input, provider failure, policy rejection,
acceptance failure, verification failure, and operational startup failure. Human-
readable messages explain the domain; exit codes let scripts react.

The CLI keeps the evidence system usable without a browser and makes every central
claim reproducible from commands that can run in CI.

### Repository evidence

- `src/agent_proof_runtime/cli.py`
- `tests/test_cli_build_week.py`
- `README.md`
- `docs/BUILD_WEEK.md`

## Chapter 19 — HTTP Surface

Mission Control's HTTP layer is intentionally smaller than a general web platform.
It exposes the operations required for a safe judge and operator path while
refusing broad host authority.

The server supports health status, approved mission listing, constrained mission
execution, run discovery, run detail, independent re-verification, report and Proof
Bundle retrieval, declared artifact retrieval, and disposable tamper actions. Its
static frontend renders those capabilities without adding separate verification
semantics.

### Health

`GET /health` provides a low-cost operational probe. In the hosted validation, it
returned:

```json
{
  "ok": true,
  "status": "healthy",
  "service": "apr-mission-control",
  "version": "0.3.0"
}
```

Health means the checked-in service started and responded. It does not prove that
every mission will pass, that run storage is durable, or that an external anchor
exists.

### Request constraints

State-changing operations require a same-origin CSRF token. Request bodies are
bounded. Host headers are validated to reduce DNS-rebinding risk. Content Security
Policy limits the browser execution surface. Run names and paths are normalized and
validated. File retrieval resolves targets beneath an approved root, rejects
traversal and symlinks, and serves only constrained content.

The service does not accept an arbitrary shell command or filesystem path from a
browser. Missions are discovered from an approved checked-in directory and parsed
under the same strict schema used by the CLI.

### Binding policy

Loopback is the default. Remote binding requires an explicit `--allow-remote` flag.
That flag changes reachability, not identity. It does not add accounts, roles,
sessions, rate limits, or tenant isolation. A remote deployment must therefore be
described as a controlled single-operator or competition demonstration.

### Evidence retrieval

Reports and raw bundles are useful because different users need different levels of
detail. The HTML report summarizes the run. Mission Control offers interactive
views. The JSON bundle remains the machine-verifiable source. Artifact endpoints
serve only files referenced by the safe run structure.

### Hosted state

Run storage is local filesystem state and may be ephemeral on hosted platforms. A
restart or redeploy can remove evidence unless the operator attaches appropriate
persistent storage. The book treats durability as an operational choice, not an
implicit guarantee of deployment.

The HTTP layer succeeds when it makes the existing evidence path accessible without
expanding the runtime into a generic remote execution service.

### Repository evidence

- `src/agent_proof_runtime/mission_control.py`
- `tests/test_mission_control.py`
- `docs/HOSTED_VALIDATION.md`

## Chapter 20 — Repository Architecture

APR's repository architecture follows a deliberate constraint: do not introduce
distributed infrastructure before the product requires it.

The current system is one Python package with a standard-library runtime. The
official OpenAI SDK is an optional dependency used only when live provider selection
requires it. Mission Control uses the standard library HTTP stack and static assets.
This keeps installation, test setup, deployment, and audit surface small.

Conceptually, the package contains:

```text
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

The repository root adds checked-in mission examples, test suites, architecture and
validation documents, a Dockerfile, Railway configuration, CI workflow, and this
book.

### Why one package

The product's hard problem is evidence semantics, not service orchestration.
Splitting the runner, verifier, UI, and storage into separate deployed services too
early would add network authentication, version coordination, retries, queues, and
state consistency before those components provide independent trust.

A monolithic package does not prevent logical separation. Providers implement a
narrow interface. The verifier has version-aware entry points. Mission Control
adapts existing functions. The gVisor backend has an explicit diagnostic boundary.
These seams can become processes later if product requirements justify it.

### Dependency discipline

Narrow dependencies reduce supply-chain and compatibility risk. Fixture execution
and verification should not fail because a model SDK is unavailable. The optional
OpenAI extra makes that boundary visible at installation time.

The project supports Python 3.11 and 3.12. Test commands can run through `unittest`
with `PYTHONPATH=src`, and normal editable installation exposes the `apr` command.

### GitHub as project history

The repository documents preserved implementation checkpoints and avoids rewriting
the Build Week lineage. Earlier bundle versions remain testable. The current active
work lives on the Build Week branch rather than pretending that unmerged work is
already present on `main`.

This provenance matters for an evidence product. Architecture decisions, validation
records, code, tests, and book claims should be traceable to preserved source rather
than reconstructed after the fact.

### Repository evidence

- `pyproject.toml`
- `docs/PRODUCT_BLUEPRINT.md` section 20
- `docs/BEFORE_BUILD_WEEK.md`
- `docs/BUILD_WEEK_CHANGELOG.md`
