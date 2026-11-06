# Deployment preparation

No deployment or paid resource provisioning is performed by this repository. Obtain approval before publishing anything or incurring charges.

## Database and backend

1. Provision managed PostgreSQL in the selected region with encrypted connections, private credentials, backup/restore procedures and retention agreed with the school.
2. Build `backend/Dockerfile`. It installs the locked Python dependencies and runs as a non-root user. The image is provided, but has not been built in this environment because Docker's daemon is unavailable.
3. Configure backend environment variables from `backend/.env.example`. Set `ENVIRONMENT=production`, `DATABASE_URL=postgresql+psycopg://...?...sslmode=require`, and `FRONTEND_ORIGIN` to the exact HTTPS frontend origin (no trailing slash).
4. Run a one-off release command **before routing traffic**: `python -m alembic upgrade head`. Migrations are explicit; app startup never creates or updates tables. Alembic's baseline migration is frozen.
5. Create the initial school privately: `python -m app.bootstrap --school "Your school" --name "Administrator name" --email "admin@school.example"`. Password entry is hidden and not stored in command history. Do not seed demo data in production.
6. Configure private S3-compatible storage: `STORAGE_BACKEND=s3`, bucket, region, optional endpoint, and server-side credentials or an instance role. Block all public bucket access. The app downloads through an authorized route and requests server-side encryption on upload.
7. Run one API process initially: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers`. The provided container uses this command. Set health checks to `/api/health`; it checks database connectivity. Restrict direct API ingress at the hosting/network layer where practical; let the frontend proxy and required operator checks through.

TLS must terminate at a trusted host or proxy. The browser uses only HTTPS frontend `/api` routes. The backend's exact-origin checks and session CSRF checks still run. Enforce host/ingress allowlists and edge rate limits in the selected hosting environment. Don't enable untrusted forwarded headers just to make rate limits appear per user.

## Frontend on Vercel

- Project root: `frontend`.
- Install: `npm ci`. Build: `npm run build`. Framework: Next.js.
- Server-side environment: `API_INTERNAL_URL=https://your-api-host.example` (no trailing slash). Changing it requires a rebuild because it is used in rewrites.
- Configure the matching backend `FRONTEND_ORIGIN` for each authorized environment. Preview URLs do not automatically receive production access or credentials.
- Do not create `NEXT_PUBLIC_` variables for database, storage or model secrets.
- `frontend/vercel.json` describes build configuration only. It does not create a deployment.

## AI configuration

School authorization, child-appropriate behavior review and an approved provider contract come first. AI is explicitly disabled by default with `AI_ENABLED=false`, even if credentials exist. Only after the user approves costs, set `AI_ENABLED=true` and configure `LLM_BASE_URL` (ending in the provider's API version prefix, usually `/v1`), `LLM_API_KEY`, `LLM_MODEL`, and actual token prices. The adapter appends `/chat/completions` and requires JSON-object mode. Restrict outbound network access and use HTTPS in production. Set model/provider spend caps as well as `AI_DAILY_LIMIT`; in-app daily limits are not a substitute for a provider budget. No paid inference has been used in verification.

## Optional local PostgreSQL

With Docker Desktop running, set a local-only password and start the database:

```powershell
$env:POSTGRES_PASSWORD = 'choose-a-local-password'
docker compose up -d db
```

Set backend `DATABASE_URL=postgresql+psycopg://nexora:...@localhost:5432/nexora` and run migrations and demo seeding. Alternatively `docker compose build api`, `docker compose run --rm api python -m alembic upgrade head`, `docker compose run --rm api python -m app.seed`, then `docker compose up -d api`. Compose is a local development configuration, not hardened production infrastructure. Use a URL-safe password or percent-encode it in database URLs.

## Release and rollback

- Run tests and build before each release. Exercise the actual deployed frontend, backend, PostgreSQL and S3 path in a private staging environment.
- Take/verify a database backup before migration. Prefer additive schema changes; app rollback does not automatically roll back database data.
- Pin the app artifact, keep migration history, and record provider/model/prompt versions.
- Monitor health, error rate, p95 latency, database load and provider budget. Current logs record method/path/status/elapsed time without request bodies or credentials.
- Configure alert delivery and ownership in the selected infrastructure. This repository does not claim external monitoring has been provisioned.
