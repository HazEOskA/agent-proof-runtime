# Build Week Demo Script

Target duration: 90 seconds. Primary recording path requires no API key.

## Before recording

```bash
python -m pip install -e .
apr run examples/build-week-mission.json --provider fixture --output .runs/build-week-demo
apr mission-control
```

Open <http://127.0.0.1:8080> and keep a terminal ready. The hosted Mission Control may be used for inspection, but the local fixture path is the reproducible judge path.

## Script

**0–12 seconds — problem**

“Agents can perform a hundred steps autonomously. But logs alone cannot prove that step thirty-seven, the output, and the acceptance result still match what actually happened.”

Show the headline: **Run autonomous work. Verify what actually happened.**

**12–25 seconds — built with Codex**

“Codex helped build the strict mission manifest, controlled artifact runtime, independent verifier, security regression tests, and disposable Tamper Lab. The model never decides whether its own proof is valid.”

Briefly show the five-stage Evidence Control Room.

**25–45 seconds — verified run**

Click **Run verified demo**. Point to:

- checked-in manifest only; no arbitrary commands or filesystem paths;
- mission `PASSED`, proof `LOCAL_VERIFIED`, anchor `UNANCHORED`;
- six deterministic acceptance checks;
- artifact hashes, event replay, Merkle root, and bundle hash.

Say: “The interface visualizes evidence. The independent CLI verifier is the source of the verdict.”

**45–70 seconds — Tamper Lab hero moment**

Click **Tamper artifact**, then show the red integrity state.

“Now I change the disposable copy. The verifier recomputes the evidence and returns `FAILED`, while the original run remains preserved and `LOCAL_VERIFIED`.”

Optionally show event or metadata tampering if time allows.

**70–82 seconds — independent CLI**

```bash
apr verify .runs/build-week-demo/proof-bundle.json
```

Show `LOCAL_VERIFIED`, `PASSED`, and `UNANCHORED`.

**82–90 seconds — honest close**

“GPT-5.6 is an optional strict Structured Output artifact provider and was validated in one controlled live run. It is not the verifier. APR proves local consistency today; external anchoring and real gVisor execution remain explicit next trust layers.”

Final line: **Don’t trust the agent. Verify the proof.**

## Controlled live-provider evidence

The optional GPT-5.6 validation is documented in `docs/LIVE_VALIDATION.md`. The demo should not expose, request, or display an API key.
