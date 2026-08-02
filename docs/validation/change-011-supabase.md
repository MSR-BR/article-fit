# Change 011 — Supabase pilot validation

Date: 2026-08-01
Project reference: `qbjhtdalhjcsmujntoni`

The ordered migrations `0002` through `0006` were applied through the authenticated Supabase SQL Editor. No credential values or private document content were used or recorded.

## Post-migration verification

| Control | Observed result |
| --- | --- |
| Required application tables present | 13 |
| Required tables missing RLS | 0 |
| Private 25 MB Storage buckets | 2 |
| Durable `analysis_jobs` queue | Present |
| Queue API access | `service_role` allowed; `authenticated` denied |
| Hosted adapter smoke test | Postgres, private Storage, and Queue passed |
| Authenticated tenant isolation | Two temporary users saw only their own workspace |
| Worker recovery | Claim, retry limit, terminal state, and acknowledgement passed |
| Synthetic hosted workflow | Gemini review and four private artifacts passed |
| Cloud Run API | Revision `article-fit-api-00001-psr`; health endpoint passed |
| Cloud Run worker | Execution `article-fit-worker-2gb2f`; health-check passed without reading queue |
| Vercel production | `dpl_DUPeDZd3jWp4XTv5185hBLJ3ziG6`; page 200 and authenticated proxy 404 passed |
| `anon` grants on sampled private tables | 0 |
| Supabase Security Advisor | 0 errors, 0 warnings, 0 suggestions |
| Supabase Performance Advisor | 0 errors, 0 warnings, 17 informational suggestions |

The verified buckets are `manuscripts` and `artifacts`; both are private. The migration grants authenticated read access only through workspace-membership predicates. Application writes and queue operations remain server-side.

The hosted smoke test used a uniquely scoped synthetic workspace and project. It confirmed PostgREST creation/read,
private PDF upload/download, and `pgmq_public` send/delete. The test deleted only the object, rows, and queue message
created by that execution. A live incompatibility in bulk Storage deletion was corrected by using the documented
single-object deletion endpoint for each explicitly scoped object key.

## Remaining validation

- Verify retention/deletion after the hosted API/worker deployment.
- Exercise and document rollback after a second known-good Cloud Run revision exists.
