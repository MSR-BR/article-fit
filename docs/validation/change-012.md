# Change 012 — Pilot validation record

Status: implementation and hosted validation in progress.

## Automated evidence

- Named email-link UI and session gate: 27 web tests pass with 92.39% line coverage.
- The callback regression is covered for PKCE `code`, `token_hash`, implicit access/refresh tokens, existing sessions, and expired callbacks. Callback credentials are removed from the browser URL after processing.
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

## Corrective finding

The first owner email delivered Supabase's hosted magic link rather than the numeric code anticipated by the original interface. The link returned to Article Fit, but the page did not complete the callback and therefore displayed the access gate again. The interface now explicitly requests a one-time link and completes the returned Supabase session automatically. This finding must be rechecked in production before beginning the owner-led artifact review.

The first corrective deployment still initiated the link through `@supabase/ssr`, whose browser client forces PKCE. Supabase documents that a PKCE callback can only be exchanged in the same browser and device where it began because the locally stored verifier is required. Email applications may open the link in another browser context, reproducing the access gate without a server error. The link request now uses a non-persistent, client-only implicit-flow client; the returned tokens are accepted by the existing browser session client, removed from the URL, stored in cookies, and independently revalidated by the Vercel proxy and Python API.

## Deployment evidence

- Commit: `c917151` on `agent/article-fit-pilot`, pushed to `origin`.
- Cloud Build: `b899ca4e-9f7d-4439-926e-d7cd86d68397`, status `SUCCESS`, tag `c12-20260801-1`.
- Cloud Run API: revision `article-fit-api-00004-hl2`, 100% traffic, health `ok`.
- Cloud Run worker health execution: `article-fit-worker-4rs5w`, completed successfully without queue access.
- Vercel production: deployment `dpl_2EVNhNHxU6wrpgXwyjppqxJmB4Xv`, status `READY`, aliased to `https://article-fit.vercel.app`.
- Post-deploy error scan: no Vercel errors and no `ERROR` entries for the API revision during the validation window.
- Email-link corrective deployment: commit `783ec3f`, Vercel deployment `dpl_EMFqyNnrpq2rCVUWAU6vCg6HZTEf`, status `READY`, production alias and web health check verified. No Vercel error entries were found in the post-deploy window; the Cloud Run image was unchanged because this correction is browser-only.
