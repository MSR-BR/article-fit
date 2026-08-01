# ADR 0001: Foundation stack and provisional MVP defaults

- Status: accepted for Change 001
- Date: 2026-07-31

## Context

Change 001 needs reproducible application shells without prematurely selecting scholarly-discovery or AI vendors. The user approved the change without supplying the operational decisions listed in `.specs/shared/assumptions.md`.

## Decision

- Use an npm-workspaces monorepo for TypeScript packages and a root Python project for the API/worker packages.
- Pin Node.js 20.20.2 and Python 3.13.14. Local Python execution requires Python 3.13; Docker is the portable fallback.
- Use hash-locked Python dependencies and npm overrides for patched Next.js transitive runtime dependencies.
- Scan final container images locally with a digest-pinned Grype image. High/critical findings with stable fixes block CI; explicit temporary exceptions require a review date and documented rationale.
- Use Next.js App Router with TypeScript and the default Node.js runtime for the web shell.
- Use FastAPI for the HTTP API and a separate Python worker process.
- Use PostgreSQL, Redis, and MinIO as local interfaces for persistence, queueing, and S3-compatible private object storage.
- Target an invitation-only pilot in the São Paulo region, subject to a later privacy/hosting review.
- Use a provisional 30-day retention period for private uploads and generated artifacts; retain security/job logs for 90 days without document content. This is configuration documentation only in Change 001.
- Accept journal name, ISSN, DOI-derived metadata, or official URL as discovery input, followed by explicit user confirmation.
- Set provisional upload limits to 50 MB and 300 pages per document. No upload behavior is implemented in this change.
- Use visible colored annotations plus a change ledger for the MVP. Native Word tracked changes remain an evaluated future enhancement.
- Defer AI and scholarly-provider selection. Zero-retention terms, credentials, licensing, and provider contracts must be approved in Change 003 or earlier if required.

## Consequences

- The foundation is locally reproducible and vendor-neutral at external provider boundaries.
- These operational defaults are reversible specifications, not promises about the final production environment.
- Change 002 must enforce privacy, retention, tenant isolation, and file limits before accepting real manuscripts.
