# Change 027 — Resource budget and cleanup

## Objective

Keep the open MVP within free-tier-friendly usage while preserving the journal memory that improves future analyses.

## Requirements

- Remove project uploads, jobs, analyses, artifacts, and audit records when their retention window ends.
- Preserve only durable journal-level editorial memory and its validated official snapshots.
- Remove audit events older than 30 days during the retention job.
- Back off browser status polling during confirmed progress plateaus, without delaying immediate stage changes.
- Keep Cloud Run at zero minimum instances, one maximum API instance, one worker task, and bounded upload sizes.

## Acceptance criteria

- A clean workspace contains no project, document, job, analysis, or artifact rows after reset.
- Journal profile memory remains available after project cleanup.
- Retention tests cover audit-event deletion.
- Web tests, full Python coverage, build, lint, typecheck, dependency audit, and production smoke checks pass.
- The production frontend and API remain available after deployment.

## Files to modify

- `apps/web/src/app/page.tsx`
- `apps/api/src/journal_matcher_api/hosted.py`
- `tests/unit/test_hosted_repositories.py`
- Resource and validation documentation

## Tests to run

- Full web and Python suites with coverage
- Lint, typecheck, build, format, boundaries, secrets, and dependency audit
- Supabase row/storage count verification
- Vercel and Cloud Run health smoke tests

## Completion checklist

- [x] Resource audit completed.
- [x] Test data removed while journal memory was preserved.
- [x] Polling backoff and audit retention implemented.
- [x] C27 API/worker/Vercel deployment completed.
- [x] Post-deploy smoke tests completed.
