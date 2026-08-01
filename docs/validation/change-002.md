# Change 002 validation evidence

Validated on 2026-07-31 against the fixed project runtimes.

## Automated results

- Python Docker quality target: 15 tests passed; 94.53% total coverage; Ruff check/format and mypy passed.
- JavaScript Docker quality target: 8 tests passed across web and contracts; ESLint and TypeScript passed.
- Web coverage: 100% statements, 80% branches, 100% functions, and 100% lines.
- Contract coverage: 100% statements, branches, functions, and lines.
- Container smoke test: web/API health checks and worker startup passed; temporary services and volumes were removed by the test harness.
- Production npm audit: 0 vulnerabilities. Image scanning passed the repository policy with no high/critical findings; medium runtime findings remain tracked under the Change 001 base-image policy.

## Acceptance coverage

- Integration tests exercise project creation, journal confirmation, PDF/DOCX ingestion, the required four slots, idempotent job creation, workspace isolation, authentication failure, duplicate-slot rejection, cancellation, and deletion.
- Unit tests exercise signature/MIME mismatch, corrupt/empty input, oversized input, page limits, EICAR rejection, extraction anchors and quality, incomplete packages, and retention purge.
- Private object keys include the workspace boundary; access queries always include the workspace predicate; originals are created with mode `0600` and cannot replace an occupied slot.
- Deletion removes original object bytes and tombstones project/document metadata. Audit data contains identifiers and hashes, not document text or credentials.

## Scope and residual limitations

This evidence validates the local pilot adapters, not a production deployment. SQLite/local filesystem, manual journal confirmation, bounded parsers, and EICAR-only scanning must be replaced or strengthened before production. Literature search, journal profiling, manuscript analysis, rewriting, and final export remain absent, as required by Change 002.
