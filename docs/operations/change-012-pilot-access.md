# Change 012 — Pilot access operations

## Access model

- Public registration is disabled in Supabase Auth.
- Operators provision named users; the application requests an email OTP with `shouldCreateUser: false`.
- The browser receives only the Supabase URL and publishable key.
- The Vercel proxy verifies the user, derives the earliest authorized `workspace_members` row, and forwards the user JWT.
- The Python API verifies that JWT with Supabase Auth and independently checks the same membership using its server-only persistence boundary.
- Hosted requests never fall back to the shared invitation token when `VERCEL_ENV=production`.

## Provisioning checklist

1. Create or confirm the user in Supabase Auth.
2. Create or confirm exactly one pilot workspace membership with the intended role.
3. Confirm public sign-up and anonymous sign-in are disabled.
4. Confirm email OTP delivery for the exact user before sharing the application URL.
5. For external reviewers, configure and verify custom SMTP before provisioning them.

## Revocation

1. Remove the user's `workspace_members` row to stop data access immediately.
2. Revoke the user's active Auth sessions or ban/delete the Auth user as appropriate.
3. Verify an existing browser session now receives HTTP 403/401.
4. Preserve audit and retention records according to the pilot policy.

## Incident response

- Pause new work by disabling the Cloud Run worker job trigger or the pilot Vercel deployment.
- Do not rotate the publishable key as a substitute for revoking a user; it is intentionally public.
- Rotate the service-role secret if it may have been exposed, update Cloud Run, and redeploy before resuming.
- Use the previous immutable Vercel deployment and Cloud Run revision as rollback targets.
