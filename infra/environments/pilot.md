# Invitation-only pilot environment

Status: partially provisioned; Vercel, Supabase schema, RLS, private buckets, queue, and the dedicated
Google Cloud project `article-fit-uff` are active. Hosted Python compute remains gated on persistence parity.

## Services

| Component | Proposed provider | Region | Exposure |
| --- | --- | --- | --- |
| Next.js web/proxy | Vercel | `gru1` | invitation-only HTTPS |
| Postgres/Auth/Queue/Storage | Supabase | `sa-east-1` | RLS/private buckets |
| FastAPI | Google Cloud Run | `us-east1` | authenticated web-proxy/service access |
| Python worker | Google Cloud Run Job | `us-east1` | no public ingress; bounded executions |

## Secret classes

- Vercel server environment: API service URL, web session secrets, publishable Supabase configuration where needed.
- API/worker secret store: Supabase server credential, Gemini key, Research Starter key, provider contact, signing secrets.
- CI secret store: scoped deploy credentials only.
- Never copy production secrets into repository files, preview logs, browser bundles, or build output.

## Release sequence

1. Provision staging resources and apply reviewed migrations.
2. Run RLS and private-storage adversarial tests.
3. Deploy immutable preview and run synthetic end-to-end tests.
4. Exercise queue retry, worker crash, deletion, backup/restore, and provider outage.
5. Promote the validated preview; do not rebuild for promotion.
6. Observe pilot metrics and retain a tested rollback target.

## Blocking items

- Replacement of SQLite/local files and shared invitation token.
- Durable workflow/queue implementation.
- Real PRL assisted-guidance run and expert review of outputs.
