# Change 011 — Supabase pilot validation

Date: 2026-08-01
Project reference: `qbjhtdalhjcsmujntoni`

The ordered migrations `0002` through `0005` were applied through the authenticated Supabase SQL Editor in one transaction. No credential values or private document content were used or recorded.

## Post-migration verification

| Control | Observed result |
| --- | --- |
| Required application tables present | 13 |
| Required tables missing RLS | 0 |
| Private 25 MB Storage buckets | 2 |
| Durable `analysis_jobs` queue | Present |
| `anon` grants on sampled private tables | 0 |
| Supabase Security Advisor | 0 errors, 0 warnings, 0 suggestions |
| Supabase Performance Advisor | 0 errors, 0 warnings, 17 informational suggestions |

The verified buckets are `manuscripts` and `artifacts`; both are private. The migration grants authenticated read access only through workspace-membership predicates. Application writes and queue operations remain server-side.

## Remaining validation

- Add an authenticated synthetic tenant-isolation exercise.
- Verify signed artifact download expiry and retention/deletion after the hosted API/worker adapter is deployed.
