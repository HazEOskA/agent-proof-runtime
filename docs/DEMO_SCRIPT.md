# Build Week Demo Script

Target duration: 90 seconds. Record the hosted Mission Studio flow in live GPT-5.6 mode without exposing any API key, environment value, browser developer tool, or raw provider response.

## Recording setup

- Use the deployed Mission Control UI at `https://agent-proof-runtime-production.up.railway.app`.
- Record at 1920x1080 or 2560x1440, 60 fps where available.
- Keep the cursor deliberate and avoid fast scrolling.
- Prepare one concise website brief before recording.
- Select **LIVE GPT-5.6** only after confirming the server reports the provider as configured.
- Keep the generated site, Evidence Control Room, and Tamper Lab available in the same uninterrupted session.

## Voiceover and shot plan

### 0–10 seconds — problem and product

**Voiceover**

“Autonomous agents can build useful software—but a polished result and an activity log do not prove what actually happened. This is Agent Proof Runtime.”

**Screen**

- Start on the Mission Studio hero.
- Hold on the product name and the main mission flow.
- Slow zoom toward the mission brief and provider controls.

### 10–28 seconds — live seven-stage execution

**Voiceover**

“I give Mission Studio a brief and select live GPT-5.6. Seven specialized stages run in sequence: planner, research, content architect, HTML builder, CSS designer, data builder, and QA. Each stage has strict structured output, bounded retries, and a fixed artifact contract.”

**Screen**

- Paste the prepared brief.
- Select **LIVE GPT-5.6**.
- Click the mission start control.
- Follow the animated agents and handoffs as they move through the seven stages.
- Do not cut away from the actual live execution state.

### 28–43 seconds — unique generated site and fail-closed boundary

**Voiceover**

“There is no template fallback: every run produces a genuinely new website, or fails closed. The generated site is only the beginning.”

**Screen**

- Click **OPEN GENERATED SITE**.
- Show the hero, navigation, at least two content sections, and responsive visual detail.
- Return to Mission Control with one clean cut.

### 43–63 seconds — deterministic proof construction

**Voiceover**

“APR validates the exact files, enforces paths, media types and size limits, runs sixteen deterministic acceptance checks, records a hash-chained event history, and builds a Proof Bundle.”

**Screen**

- Move through the APR trust gate.
- Zoom on `4/4` artifacts and `16/16` acceptance checks.
- Show the artifact hashes, event replay, Merkle root, and bundle hash.

### 63–76 seconds — independent verification

**Voiceover**

“The independent verifier then recomputes the artifacts, acceptance evidence, Merkle root, and bundle hash. The result is PASSED, LOCAL_VERIFIED, and honestly UNANCHORED.”

**Screen**

- Hold on mission `PASSED`.
- Hold on proof `LOCAL_VERIFIED`.
- Hold on anchor `UNANCHORED`.
- Keep all three labels readable in the final edit.

### 76–85 seconds — Tamper Lab hero moment

**Voiceover**

“Now the trust test. I tamper with a disposable copy. Verification immediately fails, while the original remains preserved and locally verified.”

**Screen**

- Trigger one artifact tamper case.
- Zoom on the red `FAILED` result and exact integrity reason.
- Show that the original remains `LOCAL_VERIFIED`.

### 85–90 seconds — closing doctrine

**Voiceover**

“GPT-5.6 creates the work. It never validates its own proof. Agent Proof Runtime turns autonomous execution into evidence a human can independently verify. Proof before trust.”

**Screen**

- Return to the complete mission flow.
- End on **PROOF BEFORE TRUST** and the repository/product identity.

## Full voiceover copy

Autonomous agents can build useful software—but a polished result and an activity log do not prove what actually happened. This is Agent Proof Runtime.

I give Mission Studio a brief and select live GPT-5.6. Seven specialized stages run in sequence: planner, research, content architect, HTML builder, CSS designer, data builder, and QA. Each stage has strict structured output, bounded retries, and a fixed artifact contract. There is no template fallback: every run produces a genuinely new website, or fails closed.

The generated site is only the beginning. APR validates the exact files, enforces paths, media types and size limits, runs sixteen deterministic acceptance checks, records a hash-chained event history, and builds a Proof Bundle.

The independent verifier then recomputes the artifacts, acceptance evidence, Merkle root, and bundle hash. The result is PASSED, LOCAL_VERIFIED, and honestly UNANCHORED.

Now the trust test. I tamper with a disposable copy. Verification immediately fails, while the original remains preserved and locally verified.

GPT-5.6 creates the work. It never validates its own proof. Agent Proof Runtime turns autonomous execution into evidence a human can independently verify.

Proof before trust.

## Editing constraints

- Preserve the truthful labels `PASSED`, `LOCAL_VERIFIED`, and `UNANCHORED`.
- Never imply external anchoring, hostile-code isolation, semantic truth, or independent validation by GPT-5.6.
- Do not expose the API key, request payloads, raw model responses, hidden reasoning, browser storage, or server environment.
- Use zooms only on real evidence states, generated-site details, artifact counts, acceptance counts, and tamper failure reasons.
- Keep captions inside title-safe margins and manually correct technical terms before export.
