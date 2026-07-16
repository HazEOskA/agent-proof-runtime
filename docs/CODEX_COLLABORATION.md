# Codex Collaboration

## Human architectural decisions

The human operator set the product direction and constraints:

- build a reusable agent sandbox first, with proof evidence as a valuable extension;
- keep the scope understandable and defensible rather than claiming a bank-ready
  TEE/HSM platform;
- preserve existing commits and architecture;
- retain v0.1/v0.2 compatibility and honest trust labels;
- make the competition path work without an API key;
- never persist credentials or hidden model reasoning;
- never claim Docker, gVisor, or live GPT-5.6 validation without evidence.

## Codex contributions

Codex inspected the preserved branch and existing tests, performed the gap audit,
implemented the versioned manifest/provider/runtime/verifier path, extended Mission
Control, built Tamper Lab, wrote security and compatibility tests, reviewed failure
modes, prepared documentation/deployment files, and ran local validation commands.

One review finding is illustrative: invalid UTF-8 introduced by artifact tampering
could originally escape the verifier as an exception. Codex changed that boundary to
return `FAILED` and added a regression test.

## GPT-5.6 runtime role

GPT-5.6 is an optional artifact-proposal provider behind the same interface as the
fixture. It receives a safe mission projection and returns strict Structured Output.
The APR runtime—not the model—enforces paths, media types, file limits, and checks.
The independent verifier—not the model—recalculates integrity.

The original Codex Work environment implemented this path without a live key and
covered it with an injected fake official-client shape. A separate controlled local
GPT-5.6 run on 2026-07-15 later completed with mission `PASSED`, proof
`LOCAL_VERIFIED`, anchor `UNANCHORED`, and no API key found in persisted run files.
This validates the provider integration, not external anchoring or non-repudiation.
See `LIVE_VALIDATION.md`.

## Use of official documentation

The adapter follows the official Responses API and Structured Outputs documentation:

- <https://developers.openai.com/api/docs/guides/structured-outputs>
- <https://developers.openai.com/api/reference/resources/responses/methods/create>
- <https://developers.openai.com/api/docs/guides/latest-model>

The Work environment did not expose the OpenAI documentation MCP or a `codex` binary
to install it, so official developer pages were used as the fallback source.

## What Codex did not do

- no live OpenAI request from the original unavailable-key Codex Work environment;
- no chain-of-thought capture or persistence;
- no GitHub push, pull request, or merge from the unavailable-auth environment;
- no unsupported Docker/runsc claim from that environment;
- no external anchor, HSM, TEE, or bank-production certification claim.
