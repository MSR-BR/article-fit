# C12 pilot access release manifest

## Runtime artifacts

- Source commit: `c917151` (`agent/article-fit-pilot`).
- Database migrations: `0001` through `0006`; Change 012 adds no schema migration.
- Cloud Build: `b899ca4e-9f7d-4439-926e-d7cd86d68397` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c12-20260801-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c12-20260801-1`.
- Active API revision: `article-fit-api-00004-hl2` at 100% traffic.
- Vercel deployment: `dpl_2EVNhNHxU6wrpgXwyjppqxJmB4Xv` (`READY`).

## Validation links

- Change specification: `.specs/changes/012-pilot-validation-and-access/spec.md`.
- Automated and hosted evidence: `docs/validation/change-012.md`.
- Access/revocation runbook: `docs/operations/change-012-pilot-access.md`.
- Existing retention, rollback, Supabase, and deployment evidence remains linked from Change 011.

## Rollback targets

- Vercel: prior production deployment `dpl_DUPeDZd3jWp4XTv5185hBLJ3ziG6`.
- Cloud Run: prior ready revisions remain retained; route traffic explicitly to the selected revision rather than the floating image tag.
- Database: no C12 schema change or destructive data migration requires rollback.

## Open release gates

- Owner completion of the private real-document workflow and frozen expert rubric.
- Visual/content review of all four generated products.
- External colleague validation after SMTP delivery is configured and verified.
- Final Change 005/006 release sign-off and residual-risk acceptance.
