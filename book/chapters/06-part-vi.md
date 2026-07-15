# Part VI — Operating the System Honestly

## Chapter 21 — Execution Backends

APR preserves several execution profiles because proof generation and workload
isolation are separate concerns. A system can produce internally consistent
evidence while running behind a weak isolation boundary. Stronger isolation can
reduce runtime risk without automatically creating external trust in the receipt.

### Controlled-artifact runtime

The Build Week v1 path does not execute model-generated code or shell commands. It
accepts a structured proposal and writes allowlisted text artifacts. Its run metadata
labels the backend `controlled-artifact-runtime`, the security level
`development-only`, and the network policy either `fixture-offline` or
`provider-api-only`.

This profile gains safety by refusing general execution capability. It is suitable
for demonstrating mission contracts, provider boundaries, artifact policy,
acceptance evidence, Proof Bundles, and independent verification. It is not a
sandbox for hostile arbitrary code.

### Local demonstration backend

The earlier MissionSpec v0.2 path includes `local-demo`, which runs only the worker
shipped with APR. It does not accept an arbitrary command and retains the
`development-only` label. Its purpose is to exercise the full Mission Runner flow on
a machine without Docker.

The legacy local-process harness reduces the environment, applies timeouts and basic
resource controls where available, and uses disposable workspaces. Those controls
are useful operational hygiene, but they do not block network access or protect the
host from malicious code.

### Docker + gVisor

MissionSpec v0.2 also defines a hardened `gvisor` backend. Its contract requires:

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

The adapter is fail-closed. If Docker, `runsc`, the pinned image, or another required
condition is unavailable, execution stops. It does not use ordinary Docker while
reporting a gVisor security level.

The repository contains adapter implementation and simulated tests. The recorded
environment did not include `runsc`, so real gVisor execution remains unvalidated.
The correct present-tense claim is therefore: implemented and fail-closed, but not
real-runtime validated.

### Isolation versus evidence trust

Even a correctly functioning gVisor boundary would not solve external
non-repudiation. It can constrain a workload relative to the host kernel, but the
host that stores the bundle may still alter local evidence. Conversely, an external
signature over a bundle would not prove that the workload was safely isolated.

APR tracks these axes separately:

| Axis | Current question |
|---|---|
| Workload capability | Text proposal only, built-in demo worker, or container command? |
| Isolation | Development-only process boundary or validated sandbox? |
| Network policy | Offline, provider-only, or blocked? |
| Evidence integrity | Does the bundle recompute locally? |
| External trust | Is the bundle signed or anchored outside the host? |

This separation prevents a container label, a hash, or a hosted URL from carrying
security meaning it does not actually possess.

### Repository evidence

- `docs/ARCHITECTURE_LOCK_v0.2.md`
- `src/agent_proof_runtime/gvisor.py`
- `tests/test_gvisor.py`

## Chapter 22 — Deployment Blueprint

APR's competition deployment favors a simple containerized service:

```text
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

The checked-in Dockerfile uses Python 3.12 slim, installs the package, creates a
non-root user with UID 10001, prepares the run directory, exposes port 8080, and
defines an HTTP health probe. The container starts Mission Control on `0.0.0.0` with
explicit remote opt-in.

Railway configuration selects the Dockerfile builder, uses `/health`, restarts on
failure within a finite policy, and starts the same Mission Control command. This is
a small deployment surface with no mandatory database migration.

### Fixture as the public default

Public judging should not depend on a secret or third-party service. Fixture mode
allows every user to exercise the complete evidence path. It also makes cost,
availability, and rate limits irrelevant to the core demonstration.

If live provider access is enabled, `OPENAI_API_KEY` belongs only in the backend
environment. It must never appear in frontend JavaScript, repository files,
downloaded artifacts, reports, bundles, screenshots, or example documentation. The
browser chooses only from server-allowed operations; it never receives the secret.

### Persistence

APR stores runs on the local filesystem. On many application platforms that storage
is ephemeral. A restart, migration, or redeploy may remove prior evidence. The
current hosted product states this limitation rather than implying durable audit
retention.

When evidence must survive, operators should attach an appropriate persistent
volume or export bundles and artifacts to a controlled store. Strong retention will
also require lifecycle rules, access control, encryption, backup, and deletion
policy—requirements outside the current competition slice.

### Rollback

The deployment avoids mandatory state migrations, so application rollback is
straightforward:

1. restore the previous image or repository revision;
2. restart the stateless service;
3. preserve externally exported evidence independently;
4. verify `/health` and rerun the deterministic fixture path.

A rollback should not rewrite historical Proof Bundles. Version-aware verification
allows older receipts to retain their semantics even when the application version
changes.

### Observed hosted validation

The repository records a public Railway deployment at
`https://agent-proof-runtime-production.up.railway.app`. The health endpoint returned
version `0.3.0`, the deterministic mission passed, the proof remained
`LOCAL_VERIFIED` and `UNANCHORED`, all three tamper cases failed as expected, the
untouched original re-verified, and the report opened successfully.

That observation validates the checked-in deployment path and public judge flow. It
does not create multi-user authentication, durable storage, hostile-code isolation,
or external anchoring.

### Repository evidence

- `Dockerfile`
- `railway.json`
- `docs/HOSTED_VALIDATION.md`
- `docs/PRODUCT_BLUEPRINT.md` section 22

## Chapter 23 — Testing Strategy

APR's test strategy mirrors its trust model. The project does not treat one passing
end-to-end demo as sufficient evidence. It tests contracts, deterministic logic,
negative cases, compatibility, operational interfaces, and failure containment.

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

CI runs on Python 3.11 and 3.12. It installs the package, executes the unit suite,
validates checked-in missions, runs legacy and Build Week fixture missions, verifies
their bundles, and checks the Mission Control command surface. No live API call is
required by default.

### Negative tests are product tests

For a verification system, rejection behavior is at least as important as the happy
path. Tests should prove that unknown fields, duplicate JSON keys, unsafe paths,
un-pinned images, missing `runsc`, oversized artifacts, malformed provider output,
symlinks, incorrect hashes, broken chains, wrong Merkle roots, inconsistent
acceptance evidence, and tampered metadata do not pass silently.

An adversarial test should assert the exact failure domain when practical. A generic
exception may hide that the wrong layer caught the problem or that the public API
crashed instead of returning `FAILED`.

### Determinism

The fixture provider allows byte-level reproducibility. Given the same normalized
mission, it should produce the same proposal and traverse the same evidence
contracts. Run IDs and timestamps may vary as operational metadata, but deterministic
content and checks make regression analysis possible.

Canonicalization and Merkle logic benefit from fixed vectors. As interoperability
grows, published cross-language vectors will become necessary so independent
implementations can prove identical behavior.

### Mocked versus live tests

Mocked provider tests answer whether APR constructs the expected SDK request, parses
the expected response shape, handles missing configuration, and avoids persistence
of injected secret values. They do not prove external transport.

A controlled live test answers the narrower transport question. The repository's
dated record documents one successful GPT-5.6 run after the fixture flow and local
suite were complete. Live tests remain opt-in because they require secrets, network,
cost, and external availability.

### Validation hierarchy

The strongest practical workflow is cumulative:

```text
unit contracts
-> negative/adversarial cases
-> fixture integration
-> independent verification
-> container judge path
-> hosted smoke test
-> controlled live provider test
```

No higher layer erases a lower-layer failure. A healthy deployment cannot compensate
for a broken verifier test.

### Repository evidence

- `tests/`
- `.github/workflows/ci.yml`
- `docs/BUILD_WEEK_GAP_AUDIT.md`

## Chapter 24 — Observability and Evidence

Observability and evidence overlap, but they are not synonyms. Observability helps
operators understand a running system through logs, metrics, and traces. Evidence
supports a later, bounded verification claim.

An operational log may record retries, debug messages, stack traces, and request
context. That information can be valuable during an incident, but it may be noisy,
mutable, environment-specific, and unsafe to distribute. A Proof Bundle should
contain only structured facts required for its versioned verification semantics.

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

This structure allows the verifier to recompute rather than search text logs for a
success message.

### Safe observability

More telemetry is not automatically better. APR excludes credentials, raw
authorization values, hidden reasoning, chain-of-thought, unrelated environment
variables, and uncontrolled SDK objects. Provider metadata is allowlisted. Input and
response hashes support correlation without retaining every internal detail.

Privacy and verifiability can reinforce each other when the evidence contract is
minimal. A future regulated profile will need explicit PII handling, retention, and
redaction rules, but the current product already rejects the idea that every model
trace belongs in permanent evidence.

### Correlation

The system exposes several stable identifiers for different layers:

- mission ID identifies the declared task;
- manifest hash identifies the exact normalized contract;
- run ID identifies one execution;
- provider response ID identifies the external response where available;
- event indices and step hashes identify transitions;
- bundle hash identifies the receipt state.

Using the right identifier prevents confusion between rerunning the same mission and
replaying the same evidence. Two runs may share a mission hash while having distinct
run IDs, timestamps, provider response IDs, and bundle hashes.

### Explainability without hidden reasoning

APR does not require chain-of-thought to explain execution. The manifest explains
the declared objective. Events explain transitions. Artifacts show outputs.
Acceptance records show objective evaluation. Provider metadata identifies the
interaction. The report and Mission Control organize this evidence for a human.

This is operational explainability based on observable state, not an attempt to
turn a model's private reasoning into a trusted transcript.

### Repository evidence

- `docs/PRODUCT_BLUEPRINT.md` section 24
- `docs/PROJECT_MANIFESTO.md` section 8
- `src/agent_proof_runtime/build_week_runtime.py`
