# Change 017 — Idempotent analysis persistence

Status: deployed; fresh user workflow confirmation pending.

## Production root cause

- Failed job: `07fbd576-c5cf-4c40-842d-7d27cb333992`.
- Cloud Run execution: `article-fit-worker-xvfx8`.
- Confirmed state: `failed`, stage `manuscript-analysis`, progress `62`, error `workflow-409`.
- Worker evidence: three attempts ended with `Hosted persistence conflict`.
- Project `c8027989-d4bf-433d-972c-cec689431c05` contained a partial analysis created at `2026-08-02T16:54:43.855158+00:00` with no rules and no recommendations.
- The uploaded package and official guidance were complete. The public missing-input message was incorrect.
- Root cause: guide-rule and recommendation primary keys were derived from reusable journal/profile evidence but were globally unique database keys. A later PRL analysis could therefore reuse a key already attached to an earlier analysis.

## Implementation

- Child identities are now derived from the analysis identity, record type, and original deterministic identity.
- The scoped identity is written both to the child primary key and its public JSON record, preserving recommendation decisions and downloads.
- Hosted creation always attempts idempotent child insertion, even when the parent analysis already exists, allowing partial analysis repair.
- Parent and child inserts use duplicate-safe PostgREST preferences for concurrent or repeated execution.
- AI-review recommendations use the same analysis-scoping boundary.
- A conflict after journal research now asks the user to reset and retry; internal persistence details remain hidden.
- No Supabase schema change was required.

## Automated evidence

- Web: 20 tests passed with 95.23% statement coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 111 tests passed with 90.93% total coverage.
- Total: 137 tests passed.
- The new repository regression test reconstructs an existing partial analysis and verifies that missing analysis-scoped rules and recommendations are inserted with duplicate-safe semantics.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, and diff checks passed.

## Hosted evidence

- Source commit `4e926ac` was pushed to `origin/agent/article-fit-pilot`.
- Cloud Build `d9174e65-5681-4bec-968e-ae8578f05248` completed successfully for tag `c17-20260802-1`.
- API revision `article-fit-api-00017-rih` returned `200` from `/health` and `401` from an unauthenticated private route before receiving 100% traffic.
- Worker health execution `article-fit-worker-mkwbs` completed successfully.
- Vercel preview `dpl_85icxhCNR7aahs8ok9vc4gP3go4y` returned the web health contract and authenticated to the private API.
- Vercel production `dpl_pWhZNLH7LzpsDaDKvqzctLhGzwMQ` is `READY` and aliased to `https://article-fit.vercel.app`.
- Production returned `200` for web health and `Job not found` for a valid, intentionally nonexistent UUID through the authenticated proxy.
- No error entries were recorded for API revision `article-fit-api-00017-rih` after promotion.

## Fresh-run requirement

- The failed job cannot be resumed: its source documents were deleted after terminal failure under the established privacy rule, and the project now reports an empty document list.
- A fresh upload is required to confirm the complete production workflow beyond the former 62% failure point and close the final Change 017 checklist item.
