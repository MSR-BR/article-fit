# Testing Strategy

## Test pyramid

- Unit: journal normalization, five-year filtering, deduplication, source ranking, rule precedence, change classification, and document transforms.
- Contract: API, queue messages, provider adapters, model schemas, and artifact manifests.
- Integration: database/object storage/queue, parsers, repository resolution, profile publication, and export pipeline.
- End-to-end: upload through artifact download using synthetic or licensed fixtures.
- Expert evaluation: editorial usefulness, scientific-meaning preservation, evidence correctness, and journal-fit relevance.

## Critical suites

- Security: tenant isolation, authorization, signed URL expiry, malicious files, archive bombs, parser failures, prompt injection, SSRF, secret/log leakage, and deletion.
- Provenance: no unknown sources; exact source-to-claim mapping; DOI/ISSN verification; stale/conflicting guide behavior; open-version equivalence.
- Document integrity: headings, styles, lists, tables, figures, captions, equations, footnotes, citations, tracked annotations, Unicode, and DOCX/PDF parity.
- Reliability: retries, idempotency, cancellation, timeouts, partial provider failure, queue recovery, and duplicate submissions.
- Accessibility: keyboard flow, screen-reader names, contrast, zoom, focus, and non-color change semantics.
- Performance: file limits, concurrent jobs, queue latency, provider budgets, memory use, and export duration.

## Test data

- Use synthetic manuscripts and references by default.
- Licensed/public-domain documents require recorded provenance and permitted repository storage.
- Fixtures contain no secrets, personal data, or private user content.
- Maintain golden artifacts with semantic assertions; avoid brittle whole-file binary snapshots where metadata is nondeterministic.

## Release gates

- All deterministic, contract, integration, and critical end-to-end suites pass.
- No open critical/high security defects.
- Anti-hallucination gates in `anti-hallucination-policy.md` pass.
- Export integrity has no silent content loss in the supported fixture matrix.
- Expert-review thresholds are documented and met; disagreements and limitations are reported.
- Backup/restore, deletion, rollback, and incident runbooks are exercised in staging.
