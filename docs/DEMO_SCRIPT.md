# Build Week Demo Script

Target duration: 90 seconds. No API key required.

## Before recording

```bash
python -m pip install -e .
apr run examples/build-week-mission.json --provider fixture --output .runs/build-week-demo
apr mission-control
```

Open <http://127.0.0.1:8080> and keep a terminal ready.

## Script

**0–15 seconds — problem**

“Agent logs tell us a story. They do not independently prove that the output,
policy result, and history still match. Agent Proof Runtime turns one approved
mission into evidence another verifier can recalculate.”

Show the strict Build Week mission: exact artifacts, byte limits, media types, and
deterministic checks. State that the fixture is offline but uses the live contract.

**15–35 seconds — verified run**

Open the run in Mission Control. Point to:

- provider `fixture` and model request `gpt-5.6`;
- mission `PASSED`, proof `LOCAL_VERIFIED`, anchor `UNANCHORED`;
- artifact hashes and six acceptance results;
- event replay, Merkle root, and bundle hash.

Say: “The UI only renders evidence. The CLI verifier is the source of the verdict.”

**35–65 seconds — Tamper Lab**

Click artifact, event, then metadata tampering. For each result, show `FAILED`, one
exact failure reason, and `original preserved=true`.

Say: “Each attack runs on a disposable copy. The original bundle and artifacts are
fingerprinted before and after.”

**65–80 seconds — independent CLI**

```bash
apr verify .runs/build-week-demo/proof-bundle.json
```

Show that the original remains `LOCAL_VERIFIED / UNANCHORED`.

**80–90 seconds — honest close**

“GPT-5.6 is implemented as the optional structured artifact provider, but no live
request was made in this environment. This is local proof, not HSM-backed
non-repudiation. External anchoring and hardened isolation are the roadmap.”

## Optional controlled live smoke test

Only after the official SDK is installed and `OPENAI_API_KEY` is already configured
in the environment:

```bash
APR_OPENAI_MODEL=gpt-5.6 apr run examples/build-week-mission.json --provider openai --output .runs/gpt-5-6-smoke
```
