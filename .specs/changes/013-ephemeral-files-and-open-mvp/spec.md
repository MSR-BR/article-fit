# Change 013 — Ephemeral files, journal memory, and open MVP

Status: `complete`

## Objective

Remove end-user login from the MVP, minimize storage of submitted scholarly material, and retain only a reusable, progressively improved editorial memory for each confirmed journal.

## Requirements

- The public MVP upload interface must open without Supabase Auth, email links, accounts, or passwords.
- The browser must never receive the Supabase service-role key, Gemini key, Research Starter key, Cloud Run credential, or the internal Vercel-to-API credential.
- Vercel must continue authenticating to the private API with a server-only credential and fixed MVP workspace; removing user login must not expose the Cloud Run API directly.
- Uploaded manuscripts and reference files may exist only in private temporary storage while their workflow is queued or running.
- On terminal success, original objects and extracted document rows must be deleted immediately after all validated products are generated.
- On terminal failure or cancellation, original objects and extracted document rows must be deleted when no retry remains.
- Orphaned uploads must be purged automatically no later than 24 hours after creation.
- Generated report/DOCX/PDF products may remain in private temporary storage for download for at most 24 hours, then their objects and private analysis records must be deleted.
- The interface must explain that inputs are temporary and that generated downloads expire.
- Persistent cross-run memory must be keyed by the confirmed journal identity (ISSN when available), never by user.
- Journal memory may contain only derived editorial conclusions, official requirements, public-source provenance, aggregate counts for ephemeral user-provided samples, confidence, timestamps, and a revision number.
- Journal memory must not contain uploaded bytes, extracted private text, manuscript text, filenames, private-document hashes, color-marked outputs, recommendation text tied to a manuscript, or private source identifiers.
- A later run for the same journal must load the current journal memory, merge supported new conclusions, increase its revision, and make the new revision the active memory.
- Failed or degraded evidence acquisition must not overwrite a valid journal memory.

## Assumptions

- The MVP is intentionally public; anyone with the URL can submit a job. Cost/abuse controls are a residual risk and are not equivalent to user login.
- A 24-hour product-download window is the initial MVP balance between usability and storage minimization.
- Public official guide/scope text may be processed transiently, but the durable memory stores derived rules and source metadata rather than full page snapshots.
- Exactly one durable head/current memory exists per journal. A superseded derived revision may remain only while a temporary output still references it; the 24-hour purge removes it after the last reference disappears.
- Supabase remains the database, queue, and temporary private object store; Supabase Auth is removed from the user flow.

## Acceptance criteria

- Visiting the production URL immediately displays the upload interface.
- The Vercel proxy rejects missing internal server configuration in production but does not require a browser session.
- Direct API requests without the internal credential remain unauthorized.
- Successful and terminally failed workflows leave no manuscript/reference objects or extracted private document rows.
- The scheduled purge removes expired artifacts and private per-run records through the Storage API and database boundary.
- A repeated journal run reads the current memory and publishes a higher revision without persisting private evidence identifiers.
- Profile inspection proves that no uploaded text, filename, or private-document hash is present.
- Web, API, worker, retention, privacy, security, and hosted smoke tests pass.

## Files to modify

- `.specs/changes/013-ephemeral-files-and-open-mvp/spec.md`
- `.specs/shared/architecture.md`, `.specs/shared/roadmap.md`, `.specs/shared/project-rules.md`
- `apps/web/src/app/`, `apps/web/src/lib/`, web proxy, dependencies, and tests
- `apps/api/src/journal_matcher_api/`, `apps/worker/src/journal_matcher_worker/`, and tests
- `db/migrations/`, Cloud Run retention job, retention/privacy runbooks, environment examples, and release evidence
- Vercel and Cloud Run environment configuration

## Tests to run

- Web rendering without login and proxy internal-credential tests.
- API public-MVP principal and direct unauthorized-access tests.
- Hosted/local source cleanup on success, terminal failure, cancellation, and orphan purge.
- Artifact expiry and hard-delete tests, including Storage API deletion.
- Journal-memory reuse, optimistic concurrency, derived-only privacy, and degraded-run preservation tests.
- Full formatting, lint, typecheck, unit/integration, coverage, build, boundary, secret scan, dependency audit, migration security, and hosted smoke gates.

## Completion checklist

- [x] Owner approved no end-user login for the MVP.
- [x] Owner approved ephemeral submitted files and journal-only persistent memory.
- [x] Browser authentication and email delivery flow removed.
- [x] Internal Vercel-to-API protection verified in automated tests.
- [x] Source cleanup and artifact expiry implemented and verified locally.
- [x] Journal memory reuse and private-data exclusion implemented and verified locally.
- [x] Migration/runbooks applied to the existing Supabase project.
- [x] CPD and post-deploy smoke completed.
