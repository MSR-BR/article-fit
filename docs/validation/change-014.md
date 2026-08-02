# Change 014 — Real progress and error observability

Status: complete.

## Incident findings

- The first reported run (`536bf76e-a244-4d21-88f2-76742a1febb7`) failed in the worker after three Cloud Run attempts with container exit code 1 and public code `workflow-502`. The previous release did not persist or safely log the underlying exception, so a more specific historical cause cannot be recovered.
- The second reported run (`5e8d3292-9563-4cc9-896a-7bc084580118`) actually succeeded and produced analysis `a4f01e85-c82a-177b-e16b-e6ac0eb18850` with four artifacts. The UI later showed a false timeout because the latest-analysis endpoint returned `id` while the client expected `analysisId`.
- The assisted journal scope/guide upload did not cause the red “Arquivos prontos” state.

## Implemented behavior

- The modal reports seven server-backed substeps with approximate overall and per-step percentages.
- A concise `Agora:` line alternates stage-specific messages only while the job is running.
- All spinners and activity animation stop at success or failure.
- The background action was removed.
- Failure output now includes a useful explanation, technical code, failed stage, and up to 500 characters of temporary server detail when available.
- The worker persists real workflow milestones and emits bounded structured failure logs without manuscript text, filenames, uploaded bytes, or secrets.
- The asynchronous success flow now consumes `latest-analysis.id` and exposes the generated artifacts.

## Automated evidence

- Web: 16 tests passed with 95.7% coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 106 tests passed with 90.32% total coverage.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, production dependency audit, and diff checks passed.
- Total automated tests: 128.

## Supabase evidence

- Migration `0008_job_progress_and_error_detail.sql` was applied to the existing `article fit` project (`qbjhtdalhjcsmujntoni`).
- A fresh SQL verification confirmed `jobs.error_detail` exists.
- The column remains inside the existing temporary project/job retention boundary; no submitted files or extracted manuscript content were added to persistent journal memory.

## Hosted evidence

- Source implementation commit: `896b5a9` on `agent/article-fit-pilot`.
- Cloud Build `fab7954f-6cab-41a5-ba7c-385802d1d0a1` completed successfully for tag `c14-20260802-1`.
- API revision `article-fit-api-00011-ver` passed its tagged health check and receives 100% traffic; C13 remains available at 0% as rollback.
- Worker health execution `article-fit-worker-kqlrn` completed without consuming a user queue item.
- The worker and retention jobs use image `c14-20260802-1`.
- No Cloud Run `ERROR` entries were found for the new API revision in the post-deploy window.
- Vercel production deployment `dpl_GhpZFtCFsz6rAuR38U3Wjvqmteim` is `READY` and aliased to `https://article-fit.vercel.app`.
- Production rendered the open upload interface, and its authenticated server proxy reached the private API and returned `Not Found` for an intentionally nonexistent resource.
- No Vercel error entries were found in the post-deploy window.

## Residual validation

- A new real-document run is required to observe an external-provider failure with the improved detail capture; the old first-run exception cannot be reconstructed retroactively.
- Scientific and editorial quality remains subject to the owner-led rubric in Change 005.
