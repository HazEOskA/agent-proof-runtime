# APR Mission Studio

APR Mission Studio is an isolated upstream orchestration adapter for one constrained
demonstration: turning a website brief into a four-file static artifact proposal and
handing that proposal to Agent Proof Runtime.

The agents produce the work. APR records and verifies the evidence. The independent
verifier recomputes integrity.

## Architecture

```text
User intent
  -> Mission Planner Agent
  -> Research Agent
  -> Website Builder Agent
  -> QA Agent
  -> artifact handoff
  -> APR deterministic trust gate
  -> Proof Bundle
  -> independent deterministic verifier
```

APR is not an agent and is not another participant in the upstream group. The QA
Agent is not the verifier. QA produces a deterministic upstream review summary; only
the existing APR verifier can return `LOCAL_VERIFIED` or `FAILED`. The verifier does
not call an LLM.

Mission Studio calls the existing `run_build_week_mission(...)` path with an
`ArtifactProvider`-compatible fixture. That existing runtime validates the checked-in
manifest and provider proposal, creates the run directory, materializes files,
performs acceptance checks, records the event chain, computes the Merkle root, writes
the Proof Bundle, and invokes the independent verifier. Mission Studio contains no
second proof path, verifier, cryptographic implementation, or acceptance engine.

## Supported mission type

V1 accepts exactly:

```json
{
  "mission_type": "verified_website_build",
  "brief": "Create a dark landing page for an AI security company."
}
```

The JSON object must contain exactly those two keys. The normalized brief must be
between 10 and 2000 characters. NUL and disallowed control characters are rejected.
Line endings and repeated whitespace are normalized deterministically. The brief is
always data: it is never treated as a command, path, import, program, tool definition,
or executable content.

The upstream order is fixed:

1. `planner`
2. `research`
3. `builder`
4. `qa`

Agent definitions, ordering, arbitrary mission types, arbitrary tools, arbitrary
paths, and arbitrary file creation are not configurable in v1.

## Deterministic fixture behavior

The default flow is offline and does not require `OPENAI_API_KEY`. It does not use
external APIs, network search, shell commands, subprocesses, generated JavaScript, or
user-defined tools. Identical normalized briefs produce identical website artifacts,
stage outputs, stage output hashes, handoffs, and normalized trace data.

Runtime session events include timestamps so the browser can show backend-confirmed
progress. The persisted normalized trace intentionally excludes session IDs and wall
clock timestamps.

The Research Agent output is deterministic demo content. It is not current web
research and is not evidence that any research claim is true.

## Artifact contract

The checked-in manifest is
[`examples/verified-website-build.json`](../examples/verified-website-build.json). It
declares exactly:

- `site/index.html` as `text/html`
- `site/styles.css` as `text/css`
- `site/data.json` as `application/json`
- `studio/trace.json` as `application/json`

The provider proposes exactly those four paths. The existing proposal validator
rejects missing artifacts, extra artifacts, duplicate paths, wrong media types, and
size-limit violations before APR creates the final run directory.

The website is static, responsive, and self-contained. It has semantic hero,
three-feature, and call-to-action sections. It has no external fonts, remote assets,
scripts, analytics, trackers, or network dependencies. User-derived text is HTML
escaped and is not inserted into scripts, styles, event handlers, selectors, or URLs.

Deterministic acceptance checks cover all four required files, exact file count, both
JSON files, required trace keys, stable HTML section markers, and every declared file
size limit.

## `studio/trace.json`

The normalized trace contains:

- trace schema and supported mission type;
- SHA-256 hash of the normalized brief;
- fixed agent order;
- concise stage summaries and structured outputs;
- SHA-256 hash for each stage output;
- ordered handoffs with the handed-off output hash;
- the exact artifact contract summary.

It does not persist hidden reasoning, chain-of-thought, private model reasoning, raw
model responses, environment dumps, or session-local timestamps. The recorded trace
proves integrity of recorded data, not private model reasoning.

## Proof and security boundary

Mission Studio does not prove semantic truth, research accuracy, design quality,
business correctness, reasoning quality, or that an agent made a good decision.

`LOCAL_VERIFIED` means the existing verifier recomputed the local Proof Bundle and
found its declared artifacts and recorded evidence internally consistent.
`UNANCHORED` means no external authority vouched for that bundle.

The existing protections remain in force:

- checked-in manifest and exact allowlisted relative paths;
- media-type, per-file, total-size, provider-timeout, and output-token limits;
- no arbitrary command or filesystem execution;
- traversal and symlink rejection;
- CSRF, Content Security Policy, Host-header, and DNS-rebinding protections;
- original-run preservation in Tamper Lab.

Hosted Mission Studio session state is in memory and may be ephemeral. This is a
development-only local operator interface, not production-grade multi-user security.
Real gVisor execution remains unvalidated. Hostile-code isolation is not claimed; the
fixture produces inert text artifacts and APR does not execute them.

## Run locally

From the repository root:

```powershell
python -m pip install -e .
apr mission-control --missions-dir missions --runs-dir .runs --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`, enter or load the preset website brief, and select
**START MISSION**. The browser polls backend session state. It does not synthesize
agent progress with frontend-only orchestration timers.

## Test

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The focused coverage includes request validation, determinism, exact artifact and
media-type contracts, proposal policy validation, a complete fixture run, independent
verification, targeted mutations of `site/index.html` and `studio/trace.json`,
original-run preservation, HTTP security, polling, and continued operation of the
existing Mission Control routes.
