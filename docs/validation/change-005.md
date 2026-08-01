# Change 005 validation evidence

Validation run: 2026-07-31. The release candidate is **not signed off** because blind expert review and production-like staging drills have not occurred.

## Frozen benchmark and thresholds

- The repository benchmark contains six wholly synthetic cases across six journals, four article types, DOCX/PDF, scientific invariants, reconstruction, missing declarations, prompt injection, provider outage, and conflicting official guidance.
- Rights are recorded as synthetic, no third-party content, no personal data, and repository storage permitted.
- Before scoring, the benchmark froze zero tolerance for fabricated source IDs, unsupported official requirements, invariant loss, silent content loss, and critical expert safety failures.
- The deterministic analysis p95 budget is 50 ms locally. Expert thresholds are median 4/5 per dimension, 80% usefulness/actionability ratings of 4 or 5, and Krippendorff alpha of at least 0.67.

## Automated results

- Python Docker quality target: 42 tests passed; Ruff check/format and mypy passed; total coverage 94.46% against the 90% gate.
- JavaScript Docker quality target: 11 tests passed across web and contracts; ESLint and TypeScript passed. Web coverage 97.46% statements/lines; contract coverage 100%.
- Benchmark gates passed for unknown sources, unsupported official requirements, conflicting guidance, prompt injection, scientific invariant extraction, and deterministic latency under 50 ms p95.
- Production npm audit: zero vulnerabilities.
- Grype scan: no fixed critical/high findings in web, API, or worker images. Medium/low runtime findings are recorded in the security review.
- Container smoke test: Postgres, Redis, MinIO, API, web, and worker checks passed; temporary containers, network, and volumes were removed.
- Boundary and high-confidence secret checks passed. CodeQL is configured as a CI gate.

## Integrity, privacy, and operational drills

- DOCX validation now rejects excessive archive entry/uncompressed size and path traversal.
- Complex DOCX-part preservation is tested for media and footnotes; creator/last-modifier, custom properties, and Word revision session identifiers are scrubbed.
- Accepted/modified proposal text must occur in both DOCX and PDF or artifact generation stops.
- Project deletion is tested after analysis and export; uploads, analyses, decisions, and all artifact objects are removed together.
- Authenticated download, tenant isolation, retry/idempotency, provider degradation, cancellation, retention, backup/restore, and non-destructive rollback simulation pass locally.
- The synthetic DOCX and both PDFs were rendered and every page inspected. The initial duplicate empty revision heading was fixed; the final render has no clipping, overlap, missing glyphs, or missing proposal text.
- Final DOCX accessibility audit reported zero high, medium, or low findings. Color-coded revisions also carry textual category labels.
- No external qualitative model is enabled; current model cost is therefore zero and qualitative depth remains explicitly degraded.

## Supported matrix and residual risks

- DOCX package parts are preserved while review notes are appended; PDF editable output remains a disclosed reconstruction.
- Scanned/low-extraction inputs stop. Macros, embedded objects, advanced equations, fields, drawings, and prior tracked-change meaning are not semantically edited.
- The fixed benchmark is synthetic and cannot replace blind evaluation by domain researchers and scientific editors.
- The local SQLite/filesystem backup drill does not prove managed database/object-store recovery, queue redrive, signed-download expiry, alert delivery, or deployment rollback.
- Shared invitation-token authentication, synchronous execution, bounded PDF parsing, and placeholder malware scanning prohibit uncontrolled production use.

## Blocking external gates

1. Recruit qualified blinded reviewers and score at least 12 rights-cleared manuscripts with the frozen rubric.
2. Calculate inter-reviewer agreement, adjudicate critical disagreements, and meet every frozen expert threshold.
3. Deploy the release candidate to the eventual staging stack and execute managed backup/restore, queue recovery, signed-download expiry, incident, and rollback drills.
4. Record owners and evidence, rerun scans against the exact release images, then sign off—or reject—the controlled deployment candidate.

Until all four are complete, Change 005 remains in `validation` and Change 006 must not begin.
