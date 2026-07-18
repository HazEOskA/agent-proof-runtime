# Mission Studio live OpenAI mode

Status: **LIVE-VALIDATED (2026-07-18)**

Mission Studio supports two server-selected execution modes for the fixed
`verified_website_build` mission:

- `fixture` is deterministic, offline, keyless, and is the default when the request
  omits `provider`;
- `openai` performs seven sequential OpenAI Responses API calls and requires a
  server-side `OPENAI_API_KEY`.

The browser sends only the mission type, brief, and provider selection. It never
sends, receives, stores, or displays the API key. `APR_OPENAI_MODEL` may override the
live model; the default is `gpt-5.6`.

## Seven live stages

The backend runs these calls in order:

1. Mission Planner produces the site goal, audience, sections, priorities, and
   constraints.
2. Research Agent performs model-based audience and design analysis.
3. Content Architect produces the compact copy and trust-content model.
4. HTML Builder produces only `site/index.html`.
5. CSS Designer produces only `site/styles.css`.
6. Data Builder produces only `site/data.json`.
7. QA Agent reviews the assembled artifacts and returns only a concise verdict.

Artifact stages have separate output budgets and up to three bounded model-authored
attempts for incomplete, transient, contract-invalid, or quality-floor output. A retry
receives the safe failure category and contract reason so it can regenerate the artifact
without copying the fixture. If all artifact attempts fail, the mission fails closed;
the runtime never replaces paid live output with a deterministic HTML, CSS, or data
template. QA may recover only by deterministically validating the exact model-authored
artifacts already produced. It never rewrites or substitutes them.

The live quality contract explicitly rejects the offline fixture's visual signature and
requires a brief-specific art direction, bespoke hero composition, navigation, footer,
at least four semantic sections, responsive detail, and minimum HTML/CSS development
floors. After verification, Mission Control exposes **OPEN GENERATED SITE** for the exact
run artifact rather than showing only the proof status.

This is not live web research. The pipeline uses no web search, tools, shell,
filesystem tools, code execution, or external citations. Every call uses
`store=False` and a strict JSON Schema Structured Output. There is no fallback to
fixture mode. Safety refusals, authentication failures, permission failures, and bad
requests still fail closed. Artifact generation has no deterministic template fallback.

## APR trust boundary

The upstream agents produce the work. QA is an upstream reviewer, not the verifier.
Mission Studio creates `studio/trace.json` from normalized stage evidence and hands
the exact four-file proposal to the existing APR path:

```text
artifact handoff
  -> validate_proposal(...)
  -> run_build_week_mission(...)
  -> deterministic acceptance checks
  -> Proof Bundle
  -> independent deterministic verifier
```

APR is not an agent. No second manifest schema, Proof Bundle, verifier, acceptance
engine, or cryptographic path is introduced.

The fixed final artifact contract remains:

- `site/index.html` (`text/html`)
- `site/styles.css` (`text/css`)
- `site/data.json` (`application/json`)
- `studio/trace.json` (`application/json`)

Paths, media types, file counts, and size limits are not user-configurable.

## Trace and secret handling

The trace records stage summaries, output hashes, handoffs, safe model identifiers,
response identifiers, token counts, latency, and artifact hashes and byte counts. It
does not record API keys, environment dumps, hidden reasoning, chain-of-thought, raw
SDK objects, complete raw model responses, stack traces, absolute host paths, CSRF
tokens, or duplicate copies of HTML and CSS.

Safe failure categories are returned without raw exception messages or response
bodies. They distinguish missing keys or SDKs, request failures and timeouts,
structured-output failures, stage-contract rejection, artifact-contract rejection,
and runtime failures.

`LOCAL_VERIFIED` means the existing independent verifier recomputed the recorded
Proof Bundle and found its declared artifacts and evidence internally consistent. It
does not prove semantic truth, research accuracy, design quality, or reasoning
quality. `UNANCHORED` means no external authority vouched for the bundle.

## Railway configuration

The Docker image installs the existing `openai` optional dependency with
`python -m pip install --no-cache-dir '.[openai]'`. Configure `OPENAI_API_KEY` as a
Railway service secret. Optionally configure `APR_OPENAI_MODEL`. Do not place either
value in the Dockerfile, `railway.json`, source code, test fixtures, or committed env
files.

No Railway deployment is performed as part of this implementation.

## Controlled live smoke procedure

Run this only after mock tests and an operator-approved server secret are in place:

1. Install `.[openai]` and start Mission Control locally.
2. Confirm the UI reports the server key as ready without displaying it.
3. Select **LIVE GPT-5.6**, enter a constrained website brief, and start one mission.
4. Confirm seven backend API calls and the exact 26 Mission Studio events.
5. Confirm `apr.contract_enforced`, four artifacts, 16 passing acceptance checks,
   `PASSED`, `LOCAL_VERIFIED`, and `UNANCHORED`.
6. Run the existing artifact and trace tamper checks and confirm the original remains
   preserved and independently verifiable.
7. Scan persisted files for secrets, environment values, absolute paths, raw model
   responses, hidden reasoning, and stack traces.

Until that real seven-stage procedure succeeds, the status remains **IMPLEMENTED BUT
NOT LIVE-VALIDATED**. Validation of the older single-call OpenAI artifact provider
does not count as live validation of this pipeline.
