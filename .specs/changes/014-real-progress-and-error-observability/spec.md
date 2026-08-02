# Change 014 — Real progress and error observability

Status: `approved — implementation in progress`

## Objective

Make long analyses understandable and trustworthy by reporting approximate progress from real server milestones, explaining failures, and stopping all activity indicators at terminal states.

## Requirements

- Replace the four coarse rows with bounded substeps for project creation, upload validation, journal resolution, journal research, manuscript comparison, AI editorial review, and artifact generation.
- Show an approximate percentage for the overall workflow and for every substep.
- Alternate a concise live activity line within the current server-confirmed substep.
- Never advance a server phase solely from a client timer.
- Stop the header spinner, step spinner, polling, and animated activity line on success, failure, or cancellation.
- Remove the “Continuar em segundo plano” button for this version.
- Translate known failure codes into a useful explanation while retaining the technical code and failed stage.
- Persist at most 500 characters of operational error detail in the temporary job record; delete it with the project under the existing 24-hour retention boundary.
- Fix the asynchronous-success contract so `latest-analysis.id` is used as the artifact analysis identifier.
- Add structured worker failure logging without manuscript text, filenames, uploaded bytes, or secrets.

## Acceptance criteria

- A queued analysis that succeeds displays 100%, stops all spinners, and exposes artifact links using the returned analysis `id`.
- A failed job displays the friendly explanation, server detail when available, technical code, failed phase, and no moving indicator.
- The modal contains no “Continuar em segundo plano” action.
- Percentages are derived from uploads and persisted worker milestones, not an elapsed-time simulation.
- The journal scope/guide assisted path can complete without causing a false red “Arquivos prontos” state.
- Web, contracts, API, worker, formatting, lint, typecheck, build, security, and hosted smoke tests pass.

## Files to modify

- `apps/web/src/app/page.tsx`, `page.test.tsx`, and `styles.css`.
- `apps/api/src/journal_matcher_api/main.py`, `foundation.py`, and `hosted.py`.
- `apps/worker/src/journal_matcher_worker/main.py` and worker tests.
- `packages/contracts/`, `db/migrations/`, runbooks, and release evidence.

## Tests to run

- Asynchronous job success regression with `latest-analysis.id`.
- Failed job stage/detail rendering and terminal animation checks.
- Approximate progress, live activity, and background-button absence checks.
- Worker milestone persistence and structured failure logging tests.
- Full project quality and security gates, Cloud Run health, Vercel production smoke, and post-deploy error scan.

## Completion checklist

- [x] Owner supplied the two failing production states and approved the requested behavior.
- [x] Root causes identified from Vercel, Cloud Run, job, and analysis evidence.
- [x] UI progress, terminal-state, error explanation, and asynchronous ID fixes implemented locally.
- [x] Worker milestones and bounded temporary error detail implemented locally.
- [ ] Migration applied to the existing Supabase project.
- [ ] Full automated gates pass.
- [ ] CPD and hosted smoke completed.
