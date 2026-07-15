# Hosted Deployment Validation

Date: 2026-07-15

This record documents the public hosted validation of Agent Proof Runtime Mission Control.

## Deployment

- Platform: Railway
- Public URL: `https://agent-proof-runtime-production.up.railway.app`
- Deployment source: `build-week/codex-mission-control-v1`
- Build path: checked-in `Dockerfile`
- Public mode: deterministic fixture path, no `OPENAI_API_KEY` configured

## Observed health result

`GET /health` returned:

```json
{
  "ok": true,
  "status": "healthy",
  "service": "apr-mission-control",
  "version": "0.3.0"
}
```

Railway reported the deployment as active and online, and the configured health check succeeded.

## Claim boundary

This validates that the checked-in Docker deployment starts successfully on a public host and exposes a healthy Mission Control service.

It does not create multi-user authentication, durable run storage, hostile-code isolation, external anchoring, HSM/TEE guarantees, or production security certification. Hosted run state may be ephemeral. The correct proof labels remain `LOCAL_VERIFIED` and `UNANCHORED`.
