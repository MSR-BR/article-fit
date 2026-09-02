# Database migrations

Migrations are forward-only and ordered numerically. Changes 002–004 introduced the provider-neutral model; Change 011 completes the hosted Supabase boundary with tenant RLS, private Storage buckets, and the durable `analysis_jobs` queue. Change 013 closes legacy browser/Auth reads and documents the 24-hour ephemeral boundary; application cleanup still deletes Storage objects through the Storage API, never through SQL. Change 014 adds a bounded, temporary error detail to each job so the interface can explain failures without retaining submitted content.

Never place credentials in migration files or invoke these migrations against an unverified project reference. Rehearse the full ordered set before production and use a compensating migration instead of editing an already-applied migration.
