# Change 013 — Open MVP and ephemeral-storage validation

Status: complete.

## Automated evidence

- Web: 13 tests passed, including direct rendering of the upload interface without login and server-only proxy authentication.
- Shared contracts: 6 tests passed.
- Python API/worker: 106 tests passed with 90.28% total coverage.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, hosted migration security, and integration tests passed.
- Cleanup tests cover success, terminal failure, cancellation, orphaned uploads, expired outputs, and private extracted rows.
- Journal-memory tests cover reuse, revision advancement, optimistic concurrency, degraded-run preservation, and exclusion of manuscript text, filenames, hashes, and private evidence identifiers.

## Supabase evidence

- Migration `0007_open_mvp_ephemeral_storage.sql` was applied to the existing project `qbjhtdalhjcsmujntoni` (`article fit`).
- Verification confirmed removal of the obsolete authenticated Storage policy and authenticated project grants.
- The expiry/purge index required by the retention worker is present.
- The pre-release purge inspection found zero expired projects; no submitted source files were retained by the validation run.

## Hosted runtime evidence

- Cloud Build `b90adcaf-244f-48af-8af3-e292d4a9b472` completed successfully for tag `c13-20260802-1`.
- Cloud Run API revision `article-fit-api-00005-7tf` passed its tagged health check before receiving 100% traffic.
- A direct API request without the internal credential returned HTTP 401.
- Worker execution `article-fit-worker-rmgmr` completed successfully without consuming a user queue item.
- Retention execution `article-fit-retention-h5tnh` completed successfully when invoked manually.
- Cloud Scheduler job `article-fit-retention-hourly` is enabled; its test invocation produced execution `article-fit-retention-2bf8j`, which completed successfully with one successful task.
- No `ERROR` log entries were found for API revision `article-fit-api-00005-7tf` during the post-deploy window.

## Frontend evidence

- Vercel production deployment `dpl_FxJWgLaw3dgUNfPSonUCATWZqNVC` is `READY` and aliased to `https://article-fit.vercel.app`.
- The production URL renders the journal and document upload interface directly, with no email or login gate.
- The page states that submitted documents are temporary and that generated downloads expire within 24 hours.
- A production proxy request for an intentionally nonexistent project returned HTTP 404, proving that Vercel authenticated to the private API before resource lookup.
- No Vercel error log entries were found during the post-deploy window.

## Residual MVP risks

- The public URL can be used without an account. Cost quotas, request limits, file-size limits, and operational monitoring remain the abuse-control boundary for the MVP.
- Real-document editorial quality still requires the owner-led expert assessment defined in Change 005; technical release completion is not scientific/editorial approval.
