# C13 open-MVP release manifest

## Runtime artifacts

- Source implementation commit: `332482e` on `agent/article-fit-pilot`.
- Database migrations: `0001` through `0007` in the existing Supabase project.
- Cloud Build: `b90adcaf-244f-48af-8af3-e292d4a9b472` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c13-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c13-20260802-1`.
- Active API revision: `article-fit-api-00005-7tf` at 100% traffic.
- Worker job: `article-fit-worker`.
- Retention job: `article-fit-retention`.
- Retention scheduler: `article-fit-retention-hourly` (`ENABLED`).
- Vercel production: `dpl_FxJWgLaw3dgUNfPSonUCATWZqNVC` (`READY`), aliased to `https://article-fit.vercel.app`.

## Privacy and persistence boundary

- There is no end-user login in the MVP.
- Uploaded manuscript and reference files are private and temporary; they are deleted at terminal processing or by the 24-hour purge safety net.
- Generated products are private temporary downloads with a maximum 24-hour lifetime.
- Only derived, journal-scoped editorial memory persists between runs. It excludes uploaded bytes, extracted private text, filenames, private hashes, manuscript-specific recommendations, and private evidence identifiers.

## Validation links

- Specification: `.specs/changes/013-ephemeral-files-and-open-mvp/spec.md`.
- Automated and hosted evidence: `docs/validation/change-013.md`.
- Architecture decision: `docs/decisions/0005-open-mvp-and-ephemeral-journal-memory.md`.
- Retention runbook: `docs/operations/change-002-retention.md`.

## Rollback targets

- Vercel: prior production deployment `dpl_2EVNhNHxU6wrpgXwyjppqxJmB4Xv`.
- Cloud Run: prior ready API revision `article-fit-api-00004-hl2`.
- Database migration `0007` is security-hardening and index-only; do not restore the obsolete authenticated access policies during an application rollback.
