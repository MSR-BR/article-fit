# ADR 0004: Proposed pilot hosting architecture

- Status: proposed — requires owner approval before provisioning
- Date: 2026-07-31

## Context

The local MVP uses a Next.js web app, a synchronous FastAPI API, a Python worker shell, SQLite, and private local files. Manuscript runs can include PDF extraction, scholarly lookup, official-page acquisition, Gemini generation, and four artifact exports. A production request must not depend on one browser connection or ephemeral local disk.

The invitation-only pilot is expected to handle unpublished manuscripts and should keep primary application data in São Paulo when provider configuration permits.

## Proposed decision

### Vercel

- Deploy only the Next.js web application and its authenticated server proxy to Vercel in `gru1`.
- Do not put the current synchronous end-to-end Python workflow behind one Vercel request. A long scholarly workflow must survive client disconnects, retries, duration limits, and deployment restarts.
- Keep all Gemini, Research Starter, Supabase secret/service credentials server-side. No service-role credential receives a `NEXT_PUBLIC_` prefix.
- Use preview deployments, validate the immutable preview, then promote that same artifact to the pilot alias. Keep the previous production deployment available for rollback.

### Supabase

- Create one pilot project in `sa-east-1`.
- Use Supabase Postgres for projects, journal profiles, evidence metadata, workflow state, recommendations, audit events, and artifact metadata.
- Use Supabase Auth for named invitation-only users; remove the shared bearer token before pilot access.
- Use two private Storage buckets: `manuscripts` and `artifacts`. Enforce 25 MB and PDF/DOCX MIME restrictions at bucket and application layers.
- Use user/workspace ownership in RLS predicates. `TO authenticated` alone is not authorization. Never use user-editable metadata for authorization.
- Serve downloads through short-lived signed URLs or authenticated downloads. Never make either bucket public.
- Treat `storage` tables as read-only metadata and perform upload/delete through the Storage API.
- Use a durable logged Supabase Queue (`pgmq`) for workflow jobs. Do not expose queue operations to browser clients.

### Worker/API compute

- Recommended pilot provider: Fly.io, using separate `web` and `worker` process groups in its `gru` (São Paulo) region. Render was not selected because its currently documented service regions do not include Brazil.
- The worker consumes the private Supabase queue, renews visibility while processing, persists every stage, and archives a message only after validated artifact creation.
- The API returns `202` with a workflow ID. The web UI polls or subscribes to persisted stage events; it does not keep one long request open.
- Provider calls use bounded retries, idempotency keys, quotas, and per-run cost ceilings.

## Required data controls

- 30-day upload/artifact retention with deletion jobs and user-triggered deletion.
- 90-day content-free operational/audit logs.
- Encryption in transit and provider-managed encryption at rest.
- No manuscript text, prompt, API key, signed URL, or document filename in application logs.
- DPA/privacy review before real pilot documents are uploaded.
- Restore, deletion, tenant-isolation, expired-link, worker-crash, provider-outage, and rollback drills before pilot sign-off.

## Rejected for the pilot

- SQLite or local filesystem in a serverless deployment.
- Public object buckets.
- Direct browser access using Supabase service-role credentials.
- One synchronous Vercel request for the whole analysis.
- Automatic production deployment before preview validation.

## Approval needed

- Approve Vercel + Supabase as vendors and `sa-east-1`/`gru1` as the pilot data and web regions.
- Approve Fly.io for Python API/worker compute and its pilot budget.
- Approve retention, DPA/privacy terms, pilot users, and monthly provider ceilings.
