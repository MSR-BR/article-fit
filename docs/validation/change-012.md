# Change 012 — Pilot validation record

Status: implementation and hosted validation in progress.

## Automated evidence

- Named email-OTP UI and session gate: 22 web tests pass with 93.25% line coverage.
- Vercel proxy user/workspace derivation: authenticated and unauthenticated route cases pass.
- Python API token and membership verification: 102 Python tests pass with 90.07% total coverage.
- Shared contracts: 6 tests pass with 100% coverage.
- Lint, typecheck, production build, dependency boundaries, secret scan, and production dependency audit pass; the audit reports zero vulnerabilities.
- Hosted unauthenticated and authenticated smoke tests: pending deployment.

## Hosted access bootstrap

- The named owner `marioreis@id.uff.br` was created in Supabase Auth without a password.
- The controlled workspace `11111111-1111-4111-8111-111111111111` was created in the existing Article Fit Supabase project.
- The owner membership was created with role `owner` and verified through the hosted persistence boundary.
- Public sign-up is disabled, anonymous sign-in is disabled, email auth remains enabled, and confirmed-email enforcement remains active.

## Internal expert session

The owner-led session will use private runtime files supplied outside Git. The reviewer will assess the four generated artifacts against the frozen Change 005 rubric, including editorial fit, actionable form/content improvements, manuscript anchoring, scientific-invariant preservation, citation support, and document fidelity.

No successful technical execution is recorded as expert approval until the owner completes that review. A colleague's later review remains a separate external validation round.
