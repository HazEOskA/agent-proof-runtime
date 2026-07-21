# Build Week Changelog

## Preserved checkpoint

- `f03fe35` — first Build Week Mission Control; immutable ancestor of this work.

## Final continuation

- `4b11b28` — strict Mission Manifest v1, fixture/OpenAI provider contracts,
  controlled materialization, deterministic acceptance checks, Proof Bundle v1,
  CLI dispatch, version-aware independent verification, competition-safe example.
- `122b6f1` — disposable Tamper Lab, Mission Control evidence detail and health
  route, provider indicators, exact tamper failures, mocked OpenAI/no-secret/CLI/HTTP
  and security regression coverage.
- `d0cc1f8` — keep mission outcome separate from proof validity, add hostile-provider
  policy regression coverage, and extend CI with the fixture flow.
- Later documentation/deployment commits — English competition README, provenance,
  collaboration record, demo script, audit, Dockerfile, and Railway configuration.
- `2eabbd0` — merge the final Mission Studio and live-validated seven-stage GPT-5.6
  pipeline into `main`.
- `bc8e85c` — merge the final 90-second demo voiceover documentation with explicit
  Codex and GPT-5.6 usage.
- `e0ffbd3` — raise the live CSS artifact ceiling to 1 MiB in the validator and both
  APR manifests after the final CSS Designer smoke run exposed the old 16 KiB cap.

## Compatibility retained

- `apr demo` and legacy `apr verify`;
- MissionSpec `apr.mission.v0.2` and gVisor fail-closed behavior;
- Proof Bundle v0.1/v0.2 verification semantics;
- Mission Control CSRF, CSP, Host/DNS rebinding, traversal, and symlink defenses.

No commit above was squashed into or used to rewrite `f03fe35`. The final
continuation was merged into `main` with its preserved ancestry intact.
