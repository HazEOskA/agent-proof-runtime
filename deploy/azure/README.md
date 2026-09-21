# APR 3D Control Plane — Azure preview

This directory is the Azure-only deployment layer for APR. It does not change
the proof runtime, backend contracts, or the 3D control-plane application.

## Runtime contract

- container port: `8080`
- health endpoint: `GET /health`
- process: `apr mission-control --host 0.0.0.0 --allow-remote`
- 3D bundle: `APR_CONTROL_PLANE_DIST=/app/frontend/dist`
- run evidence path: `/app/.runs`
- replicas: exactly `1`
- HTTP scale concurrency threshold: `1`
- ingress: external HTTPS; insecure HTTP disabled

The single-replica limit is deliberate. APR currently has one in-process
mission lock and session state, so horizontal scaling would violate the current
runtime assumptions.

## Files

- `Dockerfile` — Azure build entry point; same application contract as the
  repository-root container.
- `Dockerfile.dockerignore` — build-context exclusions for this Dockerfile.
- `containerapp.template.yaml` — Container Apps configuration with persistent
  Azure Files mounted at `/app/.runs`.

## Azure resources expected by the template

The template intentionally does not create infrastructure. Before it is applied,
the deployment flow must provide:

1. resource group `rg-apr-preview` in `westeurope`;
2. Azure Container Registry;
3. Container Apps managed environment;
4. user-assigned managed identity with `AcrPull` on the registry;
5. Azure Storage account + Azure Files share;
6. Container Apps environment storage binding named `apr-runs`.

The environment storage binding is what makes the `AzureFile` volume in the
template valid.

## Build contract

Run the build from the repository root so both Python and `frontend/` are in
the Docker build context:

```powershell
az acr build --registry <ACR_NAME> --image apr-3d-control-plane:<IMAGE_TAG> --file deploy/azure/Dockerfile .
```

The image is not considered validated until ACR reports a successful build.

## Container App template

Replace these placeholders before applying:

- `<USER_ASSIGNED_IDENTITY_RESOURCE_ID>`
- `<MANAGED_ENVIRONMENT_RESOURCE_ID>`
- `<ACR_LOGIN_SERVER>`
- `<IMAGE_TAG>`

Then create or update the app with Azure CLI. The resulting public FQDN is the
HTTPS endpoint used for the phone smoke test.

## Verification gates

A deployment is complete only when all of these pass:

1. ACR image build succeeds.
2. Container App revision becomes healthy.
3. `GET https://<FQDN>/health` returns HTTP 200.
4. `https://<FQDN>/control-plane` renders the 3D frontend on a phone.
5. A real APR run creates evidence under the mounted `/app/.runs` path.
6. Evidence remains present after a new Container App revision/restart.

Until those gates pass, Docker/Azure deployment status remains **UNVERIFIED**.
