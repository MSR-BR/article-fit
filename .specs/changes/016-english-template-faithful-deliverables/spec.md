# Change 016 — English, template-faithful deliverables

## Objective

Replace the MVP's Portuguese interface, rotating pseudo-live messages, plain-text report, and reconstructed manuscript outputs with an English workflow whose status is tied to confirmed server milestones and whose deliverables are readable, actionable, and faithful to the submitted manuscript.

## Requirements

- All end-user interface copy, errors, status text, artifact labels, and generated deliverables must be in English.
- Progress must be described as milestone-based, not as measured elapsed work. A stage may change only when the client or server confirms the corresponding operation.
- The current-activity line must show the single server-confirmed stage and must not rotate through a timer-driven list.
- The downloadable artifact list must contain only the revision report and revised manuscript review copies. Provenance remains internal and must not be exposed as a JSON download.
- The revision report must use a professional, paginated editorial-assessment layout inspired by the supplied reference report without copying its scientific content.
- The report must include an executive readiness verdict, evidence boundary, prioritized action plan, journal-rule compliance, journal-pattern comparison, section-by-section recommendations, detailed change cards, and source/evidence notes.
- Every recommendation must state where the problem occurs, what is expected, what is currently present when an excerpt is available, why the difference matters, and what the author should do. Proposed wording must be shown when the evidence supports it.
- The report must compare the manuscript's writing and presentation with the target journal's requirements and observed published pattern. It must not present a physics-content comparison with the reference articles as the journal-fit method.
- For a DOCX manuscript, the original OOXML package, styles, layout, headers, footers, relationships, images, equations, and black original text must be preserved; color-coded suggestions must be inserted adjacent to their anchored paragraphs where possible and otherwise in a clearly labeled review appendix.
- For a PDF manuscript, the revised PDF must retain each original page unchanged and interleave color-coded suggestion pages at the relevant page anchors. The Word review copy must preserve the original extracted text in black and clearly disclose that an editable DOCX template cannot be recovered from a PDF upload.
- Pending recommendations are suggestions and must appear in the review copies; they must not be silently omitted because the author has not yet accepted them.
- Generated DOCX XML must be well formed. Generated PDFs must be structurally valid, visually legible, and contain no internal identifiers, hashes, or raw machine-oriented ledgers in user-facing prose.
- Scientific changes must remain visibly marked as author-validation-required and must never be presented as verified findings.

## Acceptance criteria

- The web page contains no Portuguese user-facing copy and the document language is English.
- Running status displays a confirmed milestone such as “Uploading and validating files”; it does not cycle on a timer.
- The progress dialog says that progress is based on confirmed milestones and shows step states rather than fabricated substage percentages.
- A successful response exposes exactly `revision-report.pdf`, `revised-manuscript.docx`, and `revised-manuscript.pdf`.
- The report has a title page, running headers/page numbers, visual hierarchy, readable line lengths, and structured recommendation content; it is not a dump of IDs separated by pipes.
- A DOCX fixture retains its original package parts and content while suggestion text is added in color near the referenced paragraph.
- A PDF fixture produces a revised PDF whose original pages are retained and whose suggestion pages are visibly color coded.
- Pending recommendations are visible in both manuscript review formats.
- Structural validation rejects malformed DOCX XML and invalid PDFs.
- Unit, integration, contract, web, lint, type, coverage, and build gates pass.
- Rendered PDF and DOCX QA images have been inspected for clipping, overlap, broken pagination, and loss of the original manuscript appearance.

## Files to modify

- `.specs/shared/output-format.md`
- `.specs/shared/architecture.md`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/page.test.tsx`
- `apps/web/src/app/styles.css`
- `packages/contracts/src/index.ts`
- `packages/contracts/src/index.test.ts`
- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- `apps/api/src/journal_matcher_api/main.py`
- `tests/unit/test_manuscript_analysis.py`
- `tests/integration/test_manuscript_analysis_flow.py`
- release and validation evidence files created for Change 016

## Tests to run

- `npm run check`
- `npm run test`
- `npm run build`
- Python unit, integration, contract, and coverage suite through the repository test scripts
- DOCX package validation plus DOCX-to-PNG rendering
- PDF structural inspection, text extraction, PDF-to-PNG rendering, and page-by-page visual review
- Production smoke tests for health, workflow stage reporting, artifact list, and artifact downloads

## Completion checklist

- [x] English product copy implemented.
- [x] Timer-driven activity loop removed.
- [x] Milestone-based progress wording implemented.
- [x] User-facing provenance JSON removed.
- [x] Editorial report redesigned and content expanded.
- [x] DOCX-source fidelity implemented and verified.
- [x] PDF-source page fidelity implemented and verified.
- [x] Pending suggestions included in both review copies.
- [x] Automated gates pass.
- [x] Rendered artifact QA passes.
- [x] Commit, push, deployment, and production verification complete.
