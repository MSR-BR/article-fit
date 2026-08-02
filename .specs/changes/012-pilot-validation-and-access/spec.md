# Change 012 — Pilot Validation and Individual Access

Status: `approved — implementation in progress`

## Objective

Replace the shared pilot bearer token with named, invitation-only Supabase Auth access and complete the first owner-led hosted pilot validation without adding non-MVP product features.

## Requirements

- Authenticate pilot users individually with email OTP through the existing Supabase project `qbjhtdalhjcsmujntoni`.
- Keep public sign-up disabled. Only users provisioned by an operator may request a sign-in code.
- Derive the active workspace from `workspace_members`; never trust a browser-supplied workspace identifier without checking membership.
- Validate the Supabase access token and workspace membership again in the Python API, even when the request passed through Vercel.
- Keep the Supabase secret/service-role key server-only. Browser code may receive only the project URL and publishable key.
- Preserve the validated local invitation-token workflow for local automated tests, while hosted mode requires named Supabase Auth.
- Provide a minimal Portuguese sign-in/sign-out experience consistent with the existing interface.
- Run the hosted owner pilot with approved, non-committed files and record expert findings against the frozen Change 005 rubric.
- Update stale project documentation and record the production release/deployment evidence.

## Assumptions

- The first named pilot user is `marioreis@id.uff.br` and is assigned to the existing controlled-pilot workspace.
- Supabase's built-in email provider is sufficient for the project-organization owner during internal validation. External colleague access requires verified SMTP delivery before invitation.
- A successful technical run does not constitute editorial acceptance, scientific validation, or external expert validation.
- The user's manuscript and reference PDFs remain private runtime data and are never committed to Git.

## Acceptance criteria

- An unauthenticated visitor cannot access the upload page or proxy API calls.
- A provisioned user can request and verify an email OTP, sign out, and regain access without public registration.
- The Vercel proxy forwards the authenticated user's token and a workspace that the user belongs to.
- The Python API rejects invalid, expired, anonymous, or non-member credentials and prevents cross-workspace access.
- The owner can complete one hosted workflow and download all four expected artifacts.
- Authentication, tenant-isolation, secret-scan, unit, integration, build, and hosted smoke tests pass.
- Production deployment is verified and a rollback target remains available.
- Internal expert findings and any release blockers are recorded; colleague validation remains explicitly external and pending.

## Files to modify

- `.specs/changes/012-pilot-validation-and-access/spec.md`
- `.specs/changes/005-testing-and-validation/spec.md`
- `.specs/changes/006-export-or-deployment/spec.md`
- `.specs/shared/roadmap.md`
- `apps/web/src/app/`, `apps/web/src/lib/`, and associated tests/styles
- `apps/api/src/journal_matcher_api/` and authentication tests
- Environment examples, deployment configuration, release evidence, runbooks, and `README.md`

## Tests to run

- Web authentication, session, proxy, and page tests.
- API token-verification, membership, tenant-isolation, and local-compatibility tests.
- Full lint, typecheck, unit/integration test, build, boundary, secret, and production dependency audit gates.
- Hosted unauthenticated/authenticated smoke tests and one approved owner end-to-end workflow.
- Post-deploy health, logs, artifact download, retention, and rollback-target checks.

## Completion checklist

- [x] Change 012 scope approved by the owner.
- [x] Named authentication is implemented without exposing privileged credentials.
- [x] Owner identity and workspace membership are provisioned; public and anonymous sign-up are disabled.
- [x] Automated release gates pass locally; hosted smoke remains part of the deployment gate.
- [ ] Production commit, push, and immutable deployments complete.
- [ ] Owner-led hosted pilot and artifact review complete.
- [ ] Change 005/006 sign-off state and residual risks are updated.
