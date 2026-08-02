# Change 012 — Pilot validation record

Status: implementation and hosted validation in progress.

## Automated evidence

- Named email-OTP UI and session gate: 22 web tests pass with 93.25% line coverage.
- Vercel proxy user/workspace derivation: authenticated and unauthenticated route cases pass.
- Python API token and membership verification: 102 Python tests pass with 90.07% total coverage.
- Shared contracts: 6 tests pass with 100% coverage.
- Lint, typecheck, production build, dependency boundaries, secret scan, and production dependency audit pass; the audit reports zero vulnerabilities.
- Hosted unauthenticated proxy and legacy-token requests return HTTP 401.
- A temporary named owner session returned HTTP 404 through both the authenticated Vercel proxy and the member-scoped API for an intentionally nonexistent project, proving both layers passed authentication before the resource lookup.
- The same session received HTTP 403 for a non-member workspace and was revoked immediately after the smoke.

## Hosted access bootstrap

- The named owner `marioreis@id.uff.br` was created in Supabase Auth without a password.
- The controlled workspace `11111111-1111-4111-8111-111111111111` was created in the existing Article Fit Supabase project.
- The owner membership was created with role `owner` and verified through the hosted persistence boundary.
- Public sign-up is disabled, anonymous sign-in is disabled, email auth remains enabled, and confirmed-email enforcement remains active.

## Internal expert session

The owner-led session will use private runtime files supplied outside Git. The reviewer will assess the four generated artifacts against the frozen Change 005 rubric, including editorial fit, actionable form/content improvements, manuscript anchoring, scientific-invariant preservation, citation support, and document fidelity.

No successful technical execution is recorded as expert approval until the owner completes that review. A colleague's later review remains a separate external validation round.

## Deployment evidence

- Commit: `c917151` on `agent/article-fit-pilot`, pushed to `origin`.
- Cloud Build: `b899ca4e-9f7d-4439-926e-d7cd86d68397`, status `SUCCESS`, tag `c12-20260801-1`.
- Cloud Run API: revision `article-fit-api-00004-hl2`, 100% traffic, health `ok`.
- Cloud Run worker health execution: `article-fit-worker-4rs5w`, completed successfully without queue access.
- Vercel production: deployment `dpl_2EVNhNHxU6wrpgXwyjppqxJmB4Xv`, status `READY`, aliased to `https://article-fit.vercel.app`.
- Post-deploy error scan: no Vercel errors and no `ERROR` entries for the API revision during the validation window.
