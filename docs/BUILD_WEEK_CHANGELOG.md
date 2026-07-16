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
- Later documentation/deployment commit — English competition README, provenance,
  collaboration record, demo script, audit, Dockerfile, Railway configuration.

## Compatibility retained

- `apr demo` and legacy `apr verify`;
- MissionSpec `apr.mission.v0.2` and gVisor fail-closed behavior;
- Proof Bundle v0.1/v0.2 verification semantics;
- Mission Control CSRF, CSP, Host/DNS rebinding, traversal, and symlink defenses.

No commit above was squashed into `f03fe35`, and no change was merged into `main`.
