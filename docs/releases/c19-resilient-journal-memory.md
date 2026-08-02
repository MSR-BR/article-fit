# C19 resilient journal-memory release manifest

## Runtime artifacts

- Source implementation commit: pending.
- Database migrations: unchanged at `0001` through `0008`.
- Cloud Build: pending.
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c19-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c19-20260802-1`.
- Active API revision: pending.
- Worker health execution: pending.
- Vercel preview: `dpl_EHnPiryiRu1Ao84i5a3822PkkhA7` (`READY`).
- Vercel production: pending.

## Product behavior

- Provider-format drift and temporary Gemini errors are retried without discarding confirmed progress.
- A sleeping or disconnected browser does not stop the Cloud Run worker.
- Gemini refines one cumulative, versioned journal standard before each manuscript review.
- The current standard records its optimization and feedback counts without storing uploaded text.
- Each generated file accepts independent feedback that is generalized into advisory future guidance.

## Validation links

- Specification: `.specs/changes/019-resilient-journal-memory-and-artifact-feedback/spec.md`.
- Incident, automated, privacy, and visual evidence: `docs/validation/change-019.md`.

## Rollback targets

- Vercel: C18 production deployment `dpl_CMugbTY5h1u1kjAVfU4YRCJdJun8`.
- Cloud Run: C18 API revision `article-fit-api-00019-sep`, retained during promotion.
- Worker and retention jobs may be reverted to image tag `c18-20260802-1`.
- No database rollback is required.
