# Change 001 — Create Project Structure

Status: `completed — corrective hardening validated on 2026-07-31`

## Objective

Create the smallest runnable monorepo skeleton, shared contracts, local developer environment, and CI baseline needed for later vertical slices.

## Requirements

- Confirm the technology baseline and unresolved decisions in `shared/assumptions.md`.
- Create only the folders listed in the approved architecture that need executable placeholders.
- Configure one package-management strategy, pinned runtime versions, linting, formatting, type checking, tests, environment templates, and secret scanning.
- Add web, API, and worker health endpoints/commands without product features.
- Add local PostgreSQL, object-storage, and queue interfaces; local implementations may be containerized or mocked as approved.
- Define versioned base contracts for IDs, errors, job state, source evidence, and artifacts.
- Add contributor setup, architecture decision records, and CI.

## Acceptance criteria

- A clean checkout can follow documented setup and run all three application shells.
- Web/API/worker smoke tests and health checks pass.
- Lint, format check, type check, unit test, secret scan, and build run in CI.
- No real provider credentials, manuscript fixtures, discovery logic, or analysis prompts exist.
- Dependency boundaries match `shared/architecture.md` and contain no circular domain dependencies.

## Files to modify

- Root workspace manifests, lockfiles, ignore/editor/runtime configuration, environment example, and contributor README.
- `apps/web/`, `apps/api/`, `apps/worker/` skeletons.
- `packages/contracts/` base schemas.
- Minimal `infra/containers/`, `tests/`, `docs/decisions/`, and CI workflow files.
- This spec’s status/checklist after approval and completion.

Exact filenames depend on the approved stack and must be recorded before implementation.

## Tests to run

- Fresh-install reproducibility check.
- Web/API/worker smoke tests.
- Lint, formatting check, strict type checks, unit tests, build, dependency-boundary check, secret scan, and container configuration validation.

## Completion checklist

- [x] User explicitly approved Change 001.
- [x] Open stack decisions are recorded.
- [x] Skeleton and contracts are created without feature leakage.
- [x] Local setup documentation is verified from a clean state.
- [x] CI-equivalent commands and all listed tests pass.
- [x] No secrets or private/copyright-restricted fixtures are committed.
- [x] Acceptance evidence is recorded in `docs/validation/change-001.md` and status is `completed`.

## Corrective hardening

- [x] Production npm advisories are blocked at high severity and patched runtime transitives are locked.
- [x] Python production and development dependency graphs are locked with hashes.
- [x] Web, API, and worker production images use patched stable runtimes and non-root users.
- [x] A real six-service container smoke test verifies web, API, worker, PostgreSQL, Redis, and MinIO.
- [x] Digest-pinned local image scans block high/critical findings with stable fixes.
- [x] Temporary scanner exceptions are narrow, documented in version control, and review-dated.
