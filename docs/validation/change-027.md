# Change 027 validation — resource budget and cleanup

Date: 2026-08-02

## Audit findings

- Cloud Run API is configured with zero minimum instances, one maximum instance, four-request concurrency,
  CPU throttling while idle, 1 CPU, and 1 GiB memory.
- Worker is one task with batch size one; retention is a separate 512 MiB job.
- Supabase Storage buckets are private and capped at 25 MiB per object.
- Source files are deleted at terminal processing; the retention job is the safety net.
- Browser status polling previously queried every two seconds even while a stage was unchanged.
- Audit events had no expiry and could grow indefinitely.

## Cleanup performed

- Removed all project, document, job, analysis, recommendation, artifact, and audit rows from the operational
  workspace.
- Removed the synthetic test workspace.
- Verified both Storage buckets contain zero objects.
- Preserved one operational workspace, one workspace member, one journal-memory head, three compact PRL memory
  versions, and two official snapshots.

## Code changes

- Polling now resets to two seconds after progress and backs off to a ten-second maximum during plateaus.
- The retention job deletes audit events older than 30 days.

## Automated gates

- Python: 135 passed, 90.35% coverage.
- Web: 23 passed, 93.42% statement coverage.
- Build, lint, typecheck, format, boundaries, secrets, and production dependency audit passed.

## Deployment

C27 deployment and production smoke checks completed.

- Cloud Build `0deb4ac0-b5e3-4839-a266-e0a53e11f350` succeeded with tag `c27-20260802-1`.
- API revision `article-fit-api-00041-tiq` is at 100% traffic; tagged health returned `ok` and private access returned `401`.
- Worker and retention jobs use `worker:c27-20260802-1`.
- Vercel deployment `dpl_CkqR9wUCTdwKSDUBTurXVoCjHfEU` is ready at `https://article-fit.vercel.app`.
