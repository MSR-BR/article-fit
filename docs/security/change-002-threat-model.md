# Change 002 threat model

## Protected assets

- Private manuscript and reference bytes, extracted segments, hashes, job state, and journal selection.
- Workspace membership and audit metadata.

## Trust boundaries and controls

- Requests cross an invitation-auth boundary and must include a valid workspace UUID.
- Every project, document, job, object key, and audit query is workspace-scoped.
- File extensions are not trusted; PDF/DOCX signatures and declared MIME must agree.
- Inputs are capped at 25 MB and PDFs at 200 pages. Empty, corrupt, low-extraction-quality, and EICAR test files fail closed.
- Original objects are created once with mode `0600`; replacing an occupied slot is rejected.
- Logs and audit events contain identifiers and hashes, never manuscript text or invitation tokens.
- Deletion removes private object bytes and tombstones related metadata. A purge command enforces the 30-day pilot retention period.

## Residual risks

- The local malware adapter recognizes the EICAR marker; production requires an isolated full malware scanner.
- The pilot extractor is intentionally bounded and is not a fidelity-grade PDF/DOCX parser.
- The local invitation token and SQLite/filesystem adapters are development defaults, not a production identity or storage design.
