# Change 002 — Implement MVP Foundation

Status: `completed`

## Objective

Implement authentication/tenant boundaries, project creation, secure document ingestion, journal confirmation, persistent jobs, and private storage as the foundation for research and analysis.

## Requirements

- Invitation-only authentication and workspace authorization.
- Create a project with target-journal candidate and required input slots: one manuscript and three references.
- Validate MIME/signature, size/page limits, malware status, hashes, and ownership before private storage.
- Extract DOCX/PDF content with page/paragraph/section anchors and explicit extraction-quality metrics.
- Resolve journal candidates and require canonical identity confirmation.
- Persist resumable/idempotent job state and display stage progress, errors, cancellation, and retry eligibility.
- Implement retention/deletion primitives and audit events.

## Acceptance criteria

- An authorized user can complete the ingestion vertical slice with supported synthetic files.
- Cross-workspace access is denied at API, database, and object layers.
- Unsupported/corrupt/malicious/low-quality files fail safely with actionable messages.
- Exactly one manuscript and three valid reference articles are required before research starts.
- Original files remain immutable and private; deletion covers defined derivatives.
- No literature search, journal profiling, analysis, or final export is implemented.

## Files to modify

- Web project/upload/status routes and accessible components.
- API authentication, projects, documents, journals, and jobs modules.
- Worker ingestion pipeline; storage/parser/scanner adapters.
- Database migrations, contracts, synthetic fixtures, tests, and operational docs.

## Tests to run

- Unit and contract suites for validation, authorization, extraction anchors, and job state.
- Integration tests with database, storage, queue, and parser adapters.
- End-to-end happy path plus corrupt, oversized, duplicate, malicious, unauthorized, cancellation, and deletion cases.
- Accessibility and log/secret-leak tests.

## Completion checklist

- [x] Change 001 is completed and Change 002 is approved.
- [x] Threat model and retention behavior are documented.
- [x] Secure ingestion and tenant isolation are implemented.
- [x] Journal confirmation and job lifecycle work end to end.
- [x] Tests and acceptance evidence pass.
- [x] Scope excludes research and analysis features.

## Explicit pilot assumptions

- Authentication is invitation-only through a configurable local bearer-token adapter; production identity is deferred.
- SQLite and a mode-`0600` local filesystem are provider implementations for the pilot. The PostgreSQL migration records the target tenant/RLS boundary but is not yet the active runtime provider.
- The pilot limit is 25 MB per document, 200 pages per PDF, and 30-day private-document retention.
- Journal identity confirmation is manual and canonical fields are user-confirmed; external journal resolution belongs to a later approved change.
- Ingestion job state is persistent and idempotent, while upload validation/extraction executes synchronously in the local adapter.
- Malware handling recognizes the EICAR test marker. A production deployment requires an isolated scanner and higher-fidelity parsers.
