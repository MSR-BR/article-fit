# Change 011 — Hosted Persistence and Durable Processing

Status: `in progress`

## Objective

Replace the pilot's ephemeral SQLite/filesystem boundary with one secured Supabase project and prepare the Python API/worker for durable hosted processing without changing the validated local workflow.

## Requirements

- Use the existing Supabase project `qbjhtdalhjcsmujntoni` for Production, Preview, and Development during the controlled pilot.
- Store tenant metadata in Postgres, originals and generated deliverables in private Storage buckets, and workflow messages in a durable Supabase Queue.
- Enable RLS on every application table exposed through the Data API; workspace membership, not authentication alone, controls private rows.
- Keep shared journal profiles derived, versioned, content-free, and readable only to authenticated pilot users.
- Never expose database passwords, JWT secrets, secret/service-role keys, manuscript contents, or private object URLs to browser code or logs.
- Preserve SQLite/local files as a test and local-development adapter until the hosted adapter reaches parity.
- Run long analyses in a separately deployed Python worker; the Vercel request boundary must remain short-lived.
- Move the web runtime baseline to Node.js 24 before the Vercel Node.js 20 retirement date.

## Acceptance criteria

- A forward-only migration creates the missing hosted tables, indexes, RLS policies, private buckets, and durable queue idempotently.
- Automated tests reject public buckets, unscoped authenticated policies, and browser-exposed privileged credentials.
- The web project builds on the Node.js 24 baseline and a Supabase-configured preview passes smoke checks.
- The hosted API persists project/job/document metadata and private objects without SQLite or ephemeral disk.
- A durable worker can claim, update, retry, and complete a workflow after a client disconnect.
- A synthetic end-to-end run produces downloadable private artifacts and passes tenant-isolation checks.

## Files to modify

- `db/migrations/`, database validation tests, persistence/provider adapters, API/worker orchestration, deployment manifests, runtime pins, specifications, and operational documentation.

## Tests to run

- Migration static-security tests and migration rehearsal against the connected Supabase project.
- Python unit/integration suite, Ruff, mypy, web lint/typecheck/tests/build, boundary checks, and secret scan.
- Private Storage, RLS tenant-isolation, queue retry, API health, worker recovery, and synthetic end-to-end tests.

## Completion checklist

- [x] Existing Supabase project connected to all three Vercel environments.
- [x] Hosted schema, RLS, buckets, and queue implemented and verified.
- [ ] Hosted Postgres/Storage adapter implemented and verified.
- [ ] Durable API/worker deployment implemented and verified.
- [x] Node.js 24 migration validated locally and on Vercel (`dpl_4dBcxAdMV6r9rhBo1YxtEgea62wV`).
- [ ] Synthetic hosted end-to-end run passes.
- [ ] Rollback, retention, and deletion drills pass.
