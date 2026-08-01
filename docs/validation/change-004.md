# Change 004 validation evidence

Validated on 2026-07-31 against the fixed project runtimes.

## Automated results

- Python Docker quality target: 32 tests passed; Ruff check/format and mypy passed; total coverage was 94.09% against the 90% gate.
- JavaScript Docker quality target: 11 tests passed across web and contracts; ESLint and TypeScript passed.
- Web coverage: 97.46% statements/lines, 80.88% branches, and 90.9% functions.
- Contract coverage: 100% statements, branches, functions, and lines.
- Synthetic golden artifacts: DOCX, revised-manuscript PDF, revision-report PDF, and provenance manifest passed structural and privacy checks.
- The DOCX and both PDF pages were rendered and inspected individually. No clipping, overlap, illegible text, or missing accepted revision note was found.
- DOCX accessibility audit: zero high-, medium-, or low-severity findings for the synthetic fixture.

## Acceptance coverage

- Official rules are extracted only from retained official snapshots and retain source IDs, hashes, and character locators. Conflicting rules cannot drive automatic compliance.
- Recommendation records distinguish official requirements, observed patterns, and expert questions; include stable anchors, confidence, uncertainty, scientific impact, and append-only author decisions.
- A scientific-impact recommendation cannot be accepted directly. The author must provide explicit modified text before it can enter an artifact.
- Invariant checks stop generation if an original number, unit, citation, or equation disappears from the revision text.
- DOCX inputs preserve their original OOXML package and receive color-coded, category-labeled notes. Extractable PDF inputs receive a reconstructed DOCX with a visible fidelity warning.
- The report contains all nine required sections, the no-acceptance guarantee, limitations, decision ledger, profile version, and reproducibility identifiers.
- Artifacts are stored under workspace-scoped private keys with mode `0600`; API and download tests cover tenant isolation and authenticated retrieval.
- The web review supports accept, reject, author-modified decisions, generation, and authenticated browser downloads.
- Regeneration uses stable recommendation IDs and deterministic templates; timestamps remain provenance metadata rather than analytical input.

## Supported document behavior

- DOCX: original package content, styles, tables, media, footnotes, relationships, and other parts are retained; review notes are appended to `word/document.xml`.
- Text-extractable PDF: analysis is supported and the editable DOCX is labeled as reconstructed. Original PDF layout fidelity is not promised.
- Scanned or extraction-poor documents stop with an actionable diagnostic.
- Macros, embedded files, complex fields, prior tracked-change semantics, advanced equations, and drawing behavior are not interpreted or rewritten. Preservation is package-level for DOCX, not semantic editing of those features.

## Residual limitations and Change 005 boundary

- No production qualitative-model provider is configured. Deterministic guide, section, declaration, scope-question, and journal-pattern checks run; deeper language, methodology, results, discussion, conclusion, figure/table, and reference critique is explicitly reported as unavailable rather than fabricated.
- Rule extraction currently recognizes a bounded set of measurable guide phrases. Unsupported or conflicting official prose remains unresolved for author review.
- PDF extraction and reconstruction are bounded and are not publication-grade layout conversion.
- The current artifact renderer appends accepted/modified proposals as an auditable review section; it does not silently rewrite scientific prose in place.
- Blind domain-expert evaluation, adversarial expansion, cross-format golden regression thresholds, and release gating belong to Change 005 and have not started.
