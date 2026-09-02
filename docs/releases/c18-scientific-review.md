# C18 scientific-review release manifest

## Runtime artifacts

- Source implementation commit: `7821e0c` on `agent/article-fit-pilot`.
- Database migrations: unchanged at `0001` through `0008`.
- Cloud Build: `4ca7c56a-c17c-4f37-97b2-415ea33b5162` (`SUCCESS`).
- API image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/api:c18-20260802-1`.
- Worker image: `us-east1-docker.pkg.dev/article-fit-uff/article-fit/worker:c18-20260802-1`.
- Active API revision: `article-fit-api-00019-sep` at 100% traffic.
- Worker job: `article-fit-worker`; health execution `article-fit-worker-ps9r9`.
- Retention job: `article-fit-retention`.
- Vercel preview: `dpl_4NgNJPnVydP8v9rse56A3T8pFDbY` (`READY`).
- Vercel production: `dpl_CMugbTY5h1u1kjAVfU4YRCJdJun8` (`READY`), aliased to `https://article-fit.vercel.app`.

## Product behavior

- Completed progress dialogs close automatically.
- Uploaded reference excerpts participate ephemerally in the Gemini editorial comparison.
- Scientific and structural coverage is enforced before artifacts are generated.
- Reports include concrete author actions for content, validation, analysis, figures, equations, cuts, moves, and writing.
- PDF-source Word reviews preserve the visual manuscript and interleave color-coded suggestions.
- Mathematical expressions render in Word and PDF outputs.

## Validation links

- Specification: `.specs/changes/018-scientific-review-and-equation-safe-documents/spec.md`.
- Automated, visual, and hosted evidence: `docs/validation/change-018.md`.

## Rollback targets

- Vercel: C17 production deployment `dpl_pWhZNLH7LzpsDaDKvqzctLhGzwMQ`.
- Cloud Run: C17 API revision `article-fit-api-00017-rih`, retained at 0% traffic.
- Worker and retention jobs may be reverted to image tag `c17-20260802-1`.
- No database rollback is required.
