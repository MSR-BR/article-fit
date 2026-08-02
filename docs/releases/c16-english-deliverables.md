# C16 English deliverables release manifest

## Runtime artifacts

- Source implementation commit: `e10b4ab` on `agent/article-fit-pilot`.
- Database migrations: unchanged at `0001` through `0008`.
- Cloud Build: `d53969ae-b8ab-4d98-abdc-efa19bc6f84a` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c16-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c16-20260802-1`.
- Active API revision: `article-fit-api-00015-joz` at 100% traffic.
- Worker job: `article-fit-worker`; health execution `article-fit-worker-2gckl`.
- Retention job: `article-fit-retention`.
- Vercel preview: `dpl_HCWABqUiBZ7P6QzwYhhnUGkUeZg2` (`READY`).
- Vercel production: `dpl_Acp1xMRTxagwSCvZTWxvYRVsCV7T` (`READY`), aliased to `https://article-fit.vercel.app`.

## User contract

- All user-facing product and generated-document copy is English.
- Workflow stages come from confirmed client/server milestones. The numeric overall percentage is an explicitly labeled milestone estimate, not measured model progress or elapsed time.
- The current-activity message is stable for the confirmed stage and no longer rotates through a timer-driven list.
- The user receives three deliverables only: `revision-report.pdf`, `revised-manuscript.docx`, and `revised-manuscript.pdf`.
- Machine-oriented provenance remains internal and is not offered as a JSON download.
- The editorial report compares the manuscript's execution with the target journal's official requirements and observed writing/presentation pattern; it does not use reference-paper physics topics as the fit criterion.
- PDF submissions retain every original manuscript page unchanged in the revised PDF, with color-coded suggestion pages interleaved at anchored locations.
- DOCX submissions retain the original OOXML package and receive color-coded suggestions adjacent to anchored paragraphs when possible.

## Validation links

- Specification: `.specs/changes/016-english-template-faithful-deliverables/spec.md`.
- Automated, visual, and hosted evidence: `docs/validation/change-016.md`.

## Rollback targets

- Vercel: production deployment `dpl_BiS1knvg31GMHrnC38LhT1GCXs7Z`.
- Cloud Run: C15 API revision `article-fit-api-00013-jab`, retained at 0% traffic.
- No database rollback is required.
