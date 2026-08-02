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

Pending C27 Cloud Run and Vercel deployment, followed by production smoke checks.
