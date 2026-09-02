# ADR 0005: Open MVP and ephemeral journal memory

- Status: accepted; supersedes the authentication and 30-day retention parts of ADR 0004
- Date: 2026-08-02

## Decision

The Article Fit MVP has no end-user account, password, email link, or Supabase Auth screen. The public Next.js page reaches the private Cloud Run API only through the Vercel server proxy. Vercel supplies a fixed workspace ID and an internal credential that is never sent to the browser. Direct API calls without that credential remain unauthorized.

Supabase remains the application database, durable queue, and private temporary object store. Its service-role key remains server-only. Legacy browser/Auth policies are revoked by migration `0007`; no Storage bucket becomes public.

Uploaded manuscript and reference files, extracted text, filenames, and private hashes are processing material, not product data. They are hard-deleted after terminal success or cancellation and after the final failed retry. Orphans and generated artifacts are hard-deleted within 24 hours.

The durable product memory is journal-scoped, normally by ISSN. Each successful run reads the active journal profile, merges supported derived conclusions, increments the revision, and publishes a new head. It may retain official/public provenance and aggregate sample counts, but never private document identifiers or content. A degraded run cannot replace a valid memory.

## Consequences

- The MVP is easier to enter and stores far less sensitive/costly data.
- Generated downloads are temporary; users must save them within the displayed window.
- Public access creates cost and abuse exposure. Rate limits, quotas, size limits, provider budgets, and monitoring are required server-side and are separate from user authentication.
- User accounts, personal history, and recovery of prior runs are future features, not hidden MVP dependencies.
