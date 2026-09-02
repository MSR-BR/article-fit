# C17 idempotent-analysis release manifest

## Runtime artifacts

- Source implementation commit: `4e926ac` on `agent/article-fit-pilot`.
- Database migrations: unchanged at `0001` through `0008`.
- Cloud Build: `d9174e65-5681-4bec-968e-ae8578f05248` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c17-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c17-20260802-1`.
- Active API revision: `article-fit-api-00017-rih` at 100% traffic.
- Worker job: `article-fit-worker`; health execution `article-fit-worker-mkwbs`.
- Retention job: `article-fit-retention`.
- Vercel preview: `dpl_85icxhCNR7aahs8ok9vc4gP3go4y` (`READY`).
- Vercel production: `dpl_pWhZNLH7LzpsDaDKvqzctLhGzwMQ` (`READY`), aliased to `https://article-fit.vercel.app`.

## Corrected behavior

- Guide rules and recommendations receive deterministic identities scoped to their analysis.
- Reusing journal memory cannot collide with child records created by an earlier project.
- Hosted analysis creation can fill missing child records in an existing partial analysis.
- Safe retries ignore child rows already inserted for the same analysis.
- Post-research persistence failures no longer tell users that required files were missing.

## Validation links

- Specification: `.specs/changes/017-idempotent-analysis-persistence/spec.md`.
- Root-cause, automated, and hosted evidence: `docs/validation/change-017.md`.

## Rollback targets

- Vercel: C16 production deployment `dpl_Acp1xMRTxagwSCvZTWxvYRVsCV7T`.
- Cloud Run: C16 API revision `article-fit-api-00015-joz`, retained at 0% traffic.
- No database rollback is required.
