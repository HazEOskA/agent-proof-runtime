# Part III — From Model Output to Controlled Artifacts

## Chapter 9 — Provider Architecture

The provider boundary is where probabilistic generation enters APR. It is also
where the system deliberately limits that generation's authority.

Every supported provider implements one narrow conceptual transformation:

```text
Validated Mission
        ↓
Structured Artifact Proposal
+ Safe Provider Metadata
```

The provider does not receive a generic filesystem tool, a terminal, a package
manager, or permission to redefine the mission. This keeps the core evidence path
independent from any particular model and prevents the most capable component from
quietly becoming the runtime administrator.

### The deterministic fixture

The fixture provider is a first-class product component. It returns deterministic
output for the same normalized mission, requires no API key, performs no network
call, and exercises the same proposal parser, artifact policy, acceptance engine,
event model, bundle builder, verifier, report, Mission Control, and Tamper Lab as a
live provider.

This is more than convenient test data. It separates two claims that are often
confused:

- the execution-evidence system behaves correctly;
- a third-party model service is currently available and returns acceptable output.

APR can demonstrate the first without depending on the second. CI can reproduce
the complete path. A judge can run the product in a fresh environment. A failure in
fixture mode points toward APR; a failure limited to live mode points toward
configuration, transport, provider response, or external service behavior.

### The optional OpenAI provider

The OpenAI adapter uses the official Python SDK and Responses API with strict JSON
Schema Structured Outputs. The request sets `store=False`, and the adapter asks the
model for the same `ArtifactProposal` shape consumed by the fixture path. The
manifest or explicit CLI selection chooses the provider; there is no silent
fallback from a requested live run to fixture mode.

`OPENAI_API_KEY` is obtained by the SDK from the process environment at request
time. It is not copied into the mission, provider metadata, events, report, or Proof
Bundle. The optional dependency is not required for fixture execution.

The repository contains mocked tests for the official client shape, structured
response parsing, missing-key behavior, and no-secret persistence. A later dated
validation record documents one controlled GPT-5.6 request on 2026-07-15. That run
completed the declared mission with `PASSED`, produced a `LOCAL_VERIFIED` proof,
remained `UNANCHORED`, recorded five events, and passed an exact-value scan that
found no API key in persisted run files.

That validation proves transport and integration for one controlled run. It does
not make the model a verifier, create external non-repudiation, or certify future
responses.

### Safe provider metadata

APR persists only metadata needed to identify and inspect the provider interaction:

- provider identifier;
- requested and resolved model;
- response identifier;
- token usage;
- latency;
- input hash;
- normalized response hash;
- implementation status.

It excludes API keys, authorization headers, secret environment variables, hidden
reasoning, chain-of-thought, raw SDK objects, internal traces, and unrelated model
metadata. The raw proposal content becomes materialized artifacts only after policy;
it is not stored as an uncontrolled provider dump.

### Failure semantics

Provider failure is its own domain. Missing credentials, missing optional SDK,
transport errors, timeouts, malformed structured output, and unsupported provider
selection should not be misreported as an invalid manifest or failed acceptance
check. Precise failure categories make operator response possible.

The provider architecture creates a reusable seam. A future provider can be added
without weakening artifact policy or changing the verifier, provided it returns the
same bounded objects. Model choice becomes replaceable; evidence semantics remain
stable.

### Repository evidence

- `src/agent_proof_runtime/providers.py`
- `tests/test_providers.py`
- `docs/LIVE_VALIDATION.md`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` provider boundary

## Chapter 10 — Structured Artifact Proposal

A model response becomes dangerous when natural-language intent is translated
directly into host authority. APR inserts a typed proposal between generation and
side effect.

The conceptual structure is small:

```json
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

The exact JSON Schema is derived from the validated mission. This is important. A
generic schema that accepts any relative path would leave the runtime to discover
authority after generation. APR can constrain the model-facing schema to the
declared artifact set while still enforcing the contract independently afterward.
Structured Output improves shape; runtime policy supplies trust.

### Proposal is not execution

An `ArtifactProposal` is data. It is not a command list. The Build Week runtime does
not interpret content as shell, Python, JavaScript, package installation, or dynamic
tool instructions. It never takes a field such as `command` and passes it to a
subprocess. Text that looks like a command remains text inside an allowed artifact,
if and only if the artifact contract permits that content type and path.

This boundary neutralizes an entire class of provider-generated side effects. A
prompt injection may still produce undesirable content, but it cannot gain a new
write path or executable host capability through the proposal interface.

### Parsing rules

The parser rejects malformed JSON and unexpected proposal structure. It requires a
list of artifacts with the exact supported fields and types. Empty or invalid paths,
duplicate paths, unsupported media types, and non-text content fail before
materialization. The parser does not accept an "almost correct" response by guessing
what the provider intended.

Strict parsing makes provider errors visible. Repairing malformed output silently
would create ambiguity about which bytes the model returned and which bytes the
runtime invented. A later retry policy may request a corrected proposal, but each
attempt should remain a distinct, inspectable transition.

### Why content remains untrusted

JSON Schema can validate structure, not truth. A model can return valid JSON with
incorrect content. It can satisfy a required key while writing a poor explanation.
It can remain below a byte limit while omitting important details. APR therefore
does not call schema validity acceptance.

The proposal passes through three separate gates:

1. syntactic and structural parsing;
2. authorization and resource policy;
3. deterministic acceptance after bytes exist on disk.

Each gate answers a different question. Parsing asks whether the object is
well-formed. Policy asks whether the runtime is allowed to materialize it.
Acceptance asks whether the resulting files meet declared objective conditions.

### Proposal identity

The provider metadata contains hashes of the safe input projection and normalized
response. These values help correlate execution without persisting secrets or raw
internal traces. Artifact records later bind the actual materialized bytes. A
response hash and an artifact hash serve different purposes: one identifies the
normalized provider result; the other proves what currently exists in the run
directory.

The proposal layer is deliberately modest. It does not make a model safe in every
context. It makes one context understandable and enforceable: proposing bounded text
artifacts under a contract the model cannot expand.

### Repository evidence

- `src/agent_proof_runtime/providers.py`
- `src/agent_proof_runtime/mission_v1.py`
- `docs/PRODUCT_BLUEPRINT.md` section 10

## Chapter 11 — Artifact Contract

The artifact contract defines the maximum write authority available to a provider.
It is the runtime equivalent of a least-privilege capability set.

For every permitted artifact, the mission declares an exact relative POSIX path and
media type. The contract also defines required files and global limits such as
maximum file count, maximum bytes per file, and maximum total bytes. The runtime
validates the proposal against these values even when the provider used a strict
schema.

### Defense in depth

It may seem redundant to constrain the model schema and then validate again. The
redundancy is intentional. Provider-side structure is not an authorization boundary.
SDK behavior may change, a fake client may return unexpected data, a future adapter
may contain a bug, or structured output may be decoded incorrectly. Authority is
granted only by runtime policy.

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

Path controls are easy to describe and easy to get subtly wrong. Rejecting strings
that contain `..` is not enough if normalization, platform separators, symlinks, or
encoded forms can still escape the intended root. APR canonicalizes artifact paths
as relative POSIX paths at manifest and proposal boundaries. During materialization
and retrieval, resolved paths must remain inside the controlled root. Symlinks are
rejected rather than followed.

Exact membership is stronger than a broad pattern in this vertical slice. If the
contract declares `summary.md` and `result.json`, a proposal for
`notes/debug.txt` fails even though the path is relative and harmless-looking. The
provider may not invent authority.

### Resource boundaries

Byte and count limits prevent a validly structured proposal from exhausting disk or
memory through uncontrolled output. Limits are evaluated against encoded bytes, not
only character count, because persistence costs bytes. Total limits matter even
when every individual file remains under its ceiling.

The Build Week path supports text artifacts, which makes encoding and safe serving
more tractable. Binary or executable artifacts would require a broader threat model,
media handling, and potentially stronger isolation. They are not smuggled into the
current profile under a generic file abstraction.

### Materialization sequence

The controlled sequence is:

```text
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

Re-reading matters because the verifier will later evaluate bytes on disk, not an
in-memory object. The artifact record includes path, media type, byte size, and
SHA-256 digest. Those values allow independent detection of missing, changed, or
unexpected content.

### Policy failure is not provider failure

A provider can return structurally valid output that violates authority. That is an
artifact-policy failure. The distinction tells operators that transport and parsing
succeeded, but the proposal attempted something outside the mission. In a future
system, that signal may trigger provider feedback, a human review, or a security
event. It should never be collapsed into a generic exception.

The artifact contract is where APR converts a broad model capability into a narrow,
reviewable permission surface.

### Repository evidence

- `src/agent_proof_runtime/build_week_runtime.py`
- `src/agent_proof_runtime/mission_v1.py`
- `tests/test_build_week_runtime.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` runtime policy

## Chapter 12 — Acceptance Engine

After permitted artifacts exist, APR evaluates the objective conditions declared in
the mission. The acceptance engine is deterministic by design. A probabilistic
provider may create content; it does not judge whether its own content met the
contract.

The current allowlist contains six check types:

| Check | Question answered |
|---|---|
| `file_exists` | Does the declared regular file exist at the safe target? |
| `file_count` | Does the controlled artifact tree contain the expected number of regular files? |
| `contains_text` | Does a text artifact contain the required literal value? |
| `json_valid` | Can the artifact be decoded as a valid JSON value under the evaluator's rules? |
| `json_required_keys` | Is the JSON object valid and does it contain each declared key? |
| `maximum_size` | Is the artifact at or below the declared byte ceiling? |

These checks are intentionally bounded. They require no model call, shell, package
installation, or untrusted interpreter. A check is accepted only when it is declared
in the manifest and has a supported parameter shape.

### Evidence, not only status

Each acceptance result records a stable check identifier, check type, pass/fail
boolean, expected value, and safe observed value. The mission's overall acceptance
status is derived from the individual results. A failure should explain which
condition did not hold rather than returning an undifferentiated red badge.

The record is later included in the Proof Bundle, but inclusion is not enough. The
independent verifier re-reads the materialized artifacts, reruns the deterministic
evaluator, and compares the reproduced results to the recorded acceptance evidence.
Changing an acceptance status or expected value without changing the relevant
evidence should therefore fail verification.

### Mission outcome versus proof outcome

Suppose a mission requires `result.json` to contain the keys `name` and `score`, but
the provider returns valid JSON with only `name`. The `json_required_keys` check
fails. The mission outcome is `FAILED`.

If the bundle accurately records the manifest, artifact, check result, events, and
hashes, the proof can still be `LOCAL_VERIFIED`. The verifier is not claiming the
mission succeeded. It is claiming that the evidence of failure is internally
consistent.

This distinction is one of APR's most important design decisions. Verification
must not turn into a success-only mechanism. Failed execution is often where
reliable evidence matters most.

### Limits of deterministic acceptance

An allowlisted check proves only its exact predicate. `contains_text` does not prove
that surrounding prose is correct. `json_valid` does not prove that values are
truthful. `file_exists` does not prove usefulness. Even a large test suite does not
prove the absence of all defects.

The contract author should resist encoding subjective ideas as fake precision. A
human design review remains human. A legal conclusion remains outside a simple JSON
predicate. APR strengthens objective checks and preserves evidence for subjective
review; it does not erase the difference.

### Extending the engine

A future check type should satisfy strict properties before entering the allowlist:

- deterministic for the declared inputs;
- bounded in time and resources;
- safe without arbitrary execution;
- representable as structured evidence;
- independently reproducible;
- versioned so old bundles keep their meaning.

The value of the acceptance engine comes from predictable semantics, not from the
number of checks it can advertise.

### Repository evidence

- `src/agent_proof_runtime/acceptance.py`
- `src/agent_proof_runtime/validator.py`
- `tests/test_build_week_runtime.py`
- `docs/ARCHITECTURE_LOCK_BUILD_WEEK_v1.md` acceptance policy
