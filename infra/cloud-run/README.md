# Cloud Run pilot

Project: `article-fit-uff`. Region: `us-east1`, chosen for broad Cloud Run availability; private manuscript
storage remains in the existing Supabase project. API and worker use separate least-privilege service accounts.

## Cost controls

- API request-based billing, zero minimum instances, one maximum instance, CPU throttled while idle.
- Worker is a one-task Cloud Run Job, never a continuously running service.
- Worker batch size is one, with two platform retries and a one-hour hard timeout.
- No VPC connector, load balancer, static IP, Cloud SQL, or always-on compute.
- Deploy only immutable image digests after the hosted persistence tests pass.

## Secret boundary

Create Secret Manager entries for `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`,
`RESEARCH_STARTER_API_KEY`, and `JOURNAL_MATCHER_INVITE_TOKEN`. Inject them at runtime; never put values in
these manifests, build arguments, image layers, logs, Vercel browser variables, or Git.

The non-secret `SUPABASE_URL`, web origin, provider contact, and Research Starter base URL may be ordinary
server environment variables. The service-role key must never use a `NEXT_PUBLIC_` prefix.

## Release gate

Do not apply these manifests until migration `0006`, hosted repository parity, queue recovery, tenant
isolation, artifact download, deletion, and synthetic end-to-end tests pass.

## Verified pilot deployment

- API: `https://article-fit-api-468465260392.us-east1.run.app`, revision `article-fit-api-00002-jnl`.
- Worker: Cloud Run Job `article-fit-worker`, image tag `c11-20260801-3`.
- Frontend: `https://article-fit.vercel.app`, production deployment `dpl_DUPeDZd3jWp4XTv5185hBLJ3ziG6`.
- API service scaling: minimum zero (default), maximum one, concurrency four, timeout 300 seconds.
- Final worker health-check execution: `article-fit-worker-bqgzv`.
- Rollback drill: revision 2 to revision 1 and back to revision 2, with health and Vercel proxy checks passing.
