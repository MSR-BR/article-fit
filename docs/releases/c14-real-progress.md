# C14 real-progress release manifest

## Runtime artifacts

- Source implementation commit: `896b5a9` on `agent/article-fit-pilot`.
- Database migrations: `0001` through `0008` in the existing Supabase project.
- Cloud Build: `fab7954f-6cab-41a5-ba7c-385802d1d0a1` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c14-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c14-20260802-1`.
- Active API revision: `article-fit-api-00011-ver` at 100% traffic.
- Worker job: `article-fit-worker`; health execution `article-fit-worker-kqlrn`.
- Retention job: `article-fit-retention`.
- Vercel production: `dpl_GhpZFtCFsz6rAuR38U3Wjvqmteim` (`READY`), aliased to `https://article-fit.vercel.app`.

## Observable workflow contract

- Progress is approximate but tied to persisted server milestones rather than elapsed-time simulation.
- Terminal jobs stop all motion and polling.
- Error detail is bounded, operational, temporary, and excluded from journal memory.
- The generated-artifact lookup uses the endpoint's canonical analysis `id`.

## Validation links

- Specification: `.specs/changes/014-real-progress-and-error-observability/spec.md`.
- Evidence and incident findings: `docs/validation/change-014.md`.

## Rollback targets

- Vercel: prior production deployment `dpl_FxJWgLaw3dgUNfPSonUCATWZqNVC`.
- Cloud Run: prior ready API revision `article-fit-api-00005-7tf` retained at 0% traffic.
- Migration `0008` is additive and can remain during an application rollback.
