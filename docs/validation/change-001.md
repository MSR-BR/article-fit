# Change 001 validation evidence

- Date: 2026-07-31
- Result: passed, including corrective hardening

## Evidence

| Check                                | Result                                             |
| ------------------------------------ | -------------------------------------------------- |
| Clean JavaScript install (`npm ci`)  | Passed                                             |
| Format, lint, strict type checks     | Passed                                             |
| Node 20.20.2 Docker quality target   | Lint, strict types, and 5 tests passed             |
| TypeScript tests                     | 5 passed; 100% measured coverage                   |
| Next.js production build             | Passed; `/` and `/api/health` generated            |
| Python 3.13.14 Docker test target    | Passed                                             |
| Python tests                         | 4 passed; 96.67% measured coverage                 |
| Dependency-boundary and secret scans | Passed                                             |
| Docker Compose validation            | Passed                                             |
| Six-service container smoke test     | Passed                                             |
| Production npm high-severity audit   | Passed after patched transitive overrides          |
| Web, API, and worker image scans     | Passed with the temporary CPython exceptions below |

The smoke test builds the three application images, starts PostgreSQL, Redis, MinIO, web, and API, verifies their health, and executes the worker health command. It then removes its isolated containers, network, and volumes.

## Dependency and image hardening

- Node.js is pinned to 20.20.2 and Python to 3.13.14.
- Python production and development dependency graphs are hash-locked.
- Next.js-managed `postcss` and `sharp` resolve to patched versions.
- Runtime images remove package managers where practical and run as non-root users.
- The local scanner is pinned by immutable image digest and CI blocks fixable high/critical findings.

The complete npm audit still reports high-severity findings confined to the lint/coverage development toolchain. The registry's proposed remediations require ESLint 10 and Vitest 4; validation showed that ESLint 10 is not yet compatible with the React rules shipped through `eslint-config-next@16.2.12`. These packages are excluded from production installs and images. CI blocks production findings, while the development-toolchain upgrade remains a tracked compatibility task.

Grype reported `CVE-2026-11940`, `CVE-2026-15308`, and `CVE-2026-11972` in CPython 3.13.14 as high severity, while listing fixes only in Python 3.15 pre-release builds. Change 001 retains a stable runtime and records narrow exceptions in the version-controlled `.grype.yaml`, with review required by 2026-08-31. These exceptions do not cover any other package, version, or vulnerability.

## Scope confirmation

No authentication, uploads, database schema, queues, provider credentials, literature discovery, prompts, journal profiling, manuscript analysis, or document export behavior was implemented. Change 002 has not started.
