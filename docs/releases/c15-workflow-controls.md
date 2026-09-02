# C15 workflow-controls release manifest

## Runtime artifacts

- Source implementation commit: `a6a7492` on `agent/article-fit-pilot`.
- Database migrations: unchanged at `0001` through `0008`.
- Cloud Build: `53c173a8-2ba3-422e-a3b8-61922b1cc3c3` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c15-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c15-20260802-1`.
- Active API revision: `article-fit-api-00013-jab` at 100% traffic.
- Worker job: `article-fit-worker`; health execution `article-fit-worker-78bbg`.
- Retention job: `article-fit-retention`.
- Vercel production: `dpl_BiS1knvg31GMHrnC38LhT1GCXs7Z` (`READY`), aliased to `https://article-fit.vercel.app`.

## User contract

- Required identity: journal title and ISSN.
- Required official evidence: same-domain HTTPS Scope and Guide for Authors URLs plus at least 500 characters copied from each page.
- Progress never regresses.
- A running analysis can be cancelled; an idle or terminal form can be reset.
- Public error copy is actionable and non-technical.

## Validation links

- Specification: `.specs/changes/015-workflow-controls-and-required-guidance/spec.md`.
- Automated and hosted evidence: `docs/validation/change-015.md`.

## Rollback targets

- Vercel: production deployment `dpl_GhpZFtCFsz6rAuR38U3Wjvqmteim`.
- Cloud Run: C14 API revision `article-fit-api-00011-ver`, retained at 0% traffic.
- No database rollback is required.
