# Change 004 — Manuscript Analysis and Revision Outputs

Status: `completed`

## Objective

Compare the private manuscript with official requirements and the journal profile, produce reviewable multidisciplinary recommendations, and generate the required DOCX/PDF/report artifacts.

## Requirements

- Transform the versioned official guide/scope snapshots from Change 003 into structured candidate rules; validate each rule against a source ID and locator before it can drive compliance analysis.
- Check scope fit, author-guide compliance, article architecture, abstract, methods, results, discussion, conclusions, language, figures/tables, references, declarations, and layout.
- Use deterministic rules for measurable constraints and bounded model analysis for qualitative recommendations.
- Preserve original content and anchors; classify every change according to `shared/output-format.md`.
- Require author verification for scientific-meaning changes and never generate missing evidence/results/citations.
- Provide review controls to accept, reject, modify, and filter proposed changes.
- Generate colored/annotated DOCX, matching PDF, revision-report PDF, and provenance manifest.
- Validate artifact completeness, parity, citations, and privacy before download.

## Proposed scope decisions

- Change 004 owns analysis, review decisions, regeneration, and all four output artifacts. Change 006 owns deployment and production download infrastructure, not artifact semantics.
- Full editable revision is supported first for DOCX manuscripts. Text-extractable PDFs receive analysis and a visibly labeled reconstructed DOCX; scanned/image-only PDFs stop with an actionable diagnostic.
- Official rules are extracted as `candidate` records and remain unusable until deterministic provenance validation succeeds. Current official guidance outranks observed patterns; unresolved official conflicts block automatic formatting for that rule.
- Deterministic checks cover counts, required sections, declared statements, reference/figure/table presence, explicit formatting constraints, and invariant preservation. Qualitative analysis uses a provider-neutral, schema-constrained model adapter only when configured.
- The model receives bounded manuscript segments, validated profile claims, and source IDs. It cannot browse, create evidence, add citations, or change numbers, units, equations, results, ethical approvals, funding, contributions, or conflicts.
- A missing model provider degrades qualitative analysis explicitly but does not disable deterministic compliance checks. No production model vendor is selected by this change specification.
- Recommendations are immutable revisions. User decisions append a new decision event (`accepted`, `rejected`, or `modified`); they never overwrite the original recommendation or manuscript.
- `required` is reserved for a validated official rule. Observed patterns can be at most `strongly recommended`; expert suggestions can be `optional` or `question` unless a separate scientific safety concern is flagged.
- Scientific-meaning changes always require author verification and are excluded from automatic application. Artifact generation uses only accepted or user-modified proposals.
- The original manuscript and every generated revision remain separately downloadable while retained.

## Recommendation taxonomy

- Categories: `language`, `structure`, `journal-format`, `methodology-reporting`, `scientific-concern`, and `unresolved`.
- Severities: `required`, `strongly-recommended`, `optional`, and `question`.
- Bases: `official-requirement`, `observed-pattern`, and `expert-suggestion`.
- Decisions: `pending`, `accepted`, `rejected`, and `modified`.
- Every record includes stable ID, manuscript anchor, original text, proposed text or author action, rationale, evidence IDs/locators, coverage, confidence/uncertainty, scientific-impact flag, and decision history.

## Supported document matrix for the first implementation

- DOCX: paragraphs, headings, basic lists, tables, inline images, footnotes, and ordinary references are supported with preservation checks.
- PDF with extractable text: analysis is supported; editable output is explicitly reconstructed and fidelity is not guaranteed.
- Scanned PDFs, macros, embedded files, complex fields, tracked-change histories, advanced equations, and unsupported drawing objects are preserved only when technically possible or cause an explicit stop/diagnostic—never silent removal.

## Acceptance criteria

- Every recommendation has category, severity, rationale, basis, evidence/confidence, locator, and status.
- Official requirements and observed patterns are never conflated.
- Original numbers, units, equations, citations, and scientific meaning remain unchanged unless explicitly flagged and author-approved.
- DOCX/PDF/report remain navigable and consistent for the supported document matrix.
- Low-fidelity PDF reconstruction is disclosed; failure does not silently damage the manuscript.
- Outputs contain no unsupported claims, internal prompts, secrets, or cross-user content.
- A run without a complete validated journal profile or without resolvable manuscript anchors stops before recommendations are generated.
- Regeneration is deterministic for the same inputs, decisions, rule/profile version, template version, and model response fixture.

## Files to modify

- Analysis, compliance, recommendation, review, and export services.
- API/worker contracts, database migrations, and artifact storage paths.
- Web analysis/review/download interfaces.
- Templates, style assets, synthetic golden documents, evaluations, and documentation.

## Tests to run

- Rule-engine and recommendation-schema unit/contract tests.
- Scientific invariant, citation integrity, prompt-injection, privacy, and adversarial tests.
- Golden DOCX/PDF/report rendering and cross-format parity tests.
- End-to-end review decisions and regeneration tests.
- Accessibility tests for change review and color-independent semantics.

## Completion checklist

- [x] Proposed taxonomy, document matrix, and author-review semantics are approved.
- [x] Required dimensions have deterministic checks or an explicit qualitative-model degradation notice.
- [x] Scientific safeguards and provenance validators pass.
- [x] Four deliverables conform to the output specification.
- [x] Supported/unsupported document features are documented.
- [x] Automated and golden-artifact acceptance evidence is recorded; blind expert validation remains in Change 005.
