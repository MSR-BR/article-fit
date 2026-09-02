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
`RESEARCH_STARTER_ARTICLE_FIT_API_KEY`, and `JOURNAL_MATCHER_INVITE_TOKEN`. The legacy `RESEARCH_STARTER_API_KEY` remains a temporary fallback during migration. Inject them at runtime; never put values in
these manifests, build arguments, image layers, logs, Vercel browser variables, or Git.

The non-secret `SUPABASE_URL`, web origin, provider contact, and Research Starter base URL may be ordinary
server environment variables. The service-role key must never use a `NEXT_PUBLIC_` prefix.

## Release gate

Do not apply these manifests until migration `0008`, hosted repository parity, queue recovery, ephemeral
isolation, artifact download, deletion, and synthetic end-to-end tests pass.

## Open MVP and retention

- Set `JOURNAL_MATCHER_PUBLIC_MVP=true` only on the API. The browser still reaches it through Vercel, which supplies the server-only internal credential and fixed workspace.
- The worker job processes durable queue messages. The separate `article-fit-retention` job uses the same image and service account with `--purge-expired`; it also removes audit events older than 30 days.
- Cloud Scheduler invokes `article-fit-retention` hourly with an OIDC-authenticated request. The 24-hour window is a maximum; source files are normally deleted much earlier at terminal processing.
- Superseded journal-memory revisions are pruned when no temporary analysis still references them. One current head remains per journal.

## Verified pilot deployment

- API: `https://article-fit-api-xstipge7eq-ue.a.run.app`, revision `article-fit-api-00039-jug` at 100% traffic.
- Worker: Cloud Run Job `article-fit-worker`, image tag `c26-20260802-1`; hosted PRL execution completed successfully.
- Retention: Cloud Run Job `article-fit-retention`; manual execution `article-fit-retention-h5tnh` and scheduled execution `article-fit-retention-2bf8j` completed successfully.
- Scheduler: `article-fit-retention-hourly`, enabled in `us-east1`, schedule `17 * * * *`, timezone `America/Sao_Paulo`.
- Frontend: `https://article-fit.vercel.app`, production deployment `dpl_Gc9WSHQzCz8j6yqppEELzH7KDWxR`.
- API service scaling: minimum zero (default), maximum one, concurrency four, timeout 300 seconds.
- Rollback target: retained API revision `article-fit-api-00037-xiw`.
- Access: the public MVP has no end-user login; Vercel supplies the server-only credential and direct unauthenticated API access remains blocked.

Verify Research Starter credential rotations with `GET https://researchstarter.vercel.app/api/v1/auth-check` before removing the previous key.
