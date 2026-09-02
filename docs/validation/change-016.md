# Change 016 — English, template-faithful deliverables

Status: complete.

## Findings corrected

- The earlier progress stages represented real state changes, but the numeric values were manually weighted milestones rather than measured computational completion. The interface now discloses this distinction.
- The earlier “Now” line used a timer to rotate generic activity messages. This created the appearance of an internal loop even when the server stage had not changed. The timer and rotating list were removed.
- `provenance-manifest.json` was machine-oriented evidence with no end-user value. It remains internal and is no longer generated or exposed as a deliverable.
- The earlier revision report was a plain ledger with raw identifiers and insufficient editorial hierarchy, diagnosis, and author actions.
- The earlier manuscript outputs reconstructed extracted text and therefore lost the submitted scientific layout.

## Implemented behavior

- The application, error copy, stage labels, metadata, and generated deliverables are English.
- Progress advances monotonically through confirmed workflow milestones. The single active-stage message changes only when the confirmed stage changes.
- The redesigned editorial report includes a title page, executive verdict, readiness dashboard, evidence boundary, prioritized action plan, official-guide compliance, journal-pattern comparison, detailed revision cards, scientific-validation warnings, and a submission gate.
- Each detailed recommendation identifies the location, current manuscript evidence when available, the journal expectation, why it matters, and an executable author action or proposed wording.
- Reference papers are used to learn editorial architecture, writing, presentation, and methodological depth—not to compare physics topics or results.
- A PDF manuscript produces a revised PDF containing every original page without modification plus blue editorial suggestion pages and red author-validation warnings at anchored locations.
- A DOCX manuscript keeps the original OOXML package and inserts colored suggestion paragraphs near resolvable paragraph anchors; unresolved manuscript-level suggestions appear in a labeled review appendix.
- Pending suggestions are visible in both review formats.
- DOCX XML and PDF structure are validated before artifacts are released.

## Automated evidence

- Web: 19 tests passed with 94.82% statement coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 110 tests passed with 90.83% total coverage.
- Total: 135 tests passed.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, production dependency audit, and diff checks passed.

## Visual artifact evidence

- The professional report was rendered to seven pages and inspected at the cover, executive dashboard, action plan, and detailed-recommendation sections. The title wrapping was corrected and rerendered; no clipping or overlap remained.
- The revised PDF generated from the 18-page PRL-style fixture contained 25 pages: original two-column scientific pages remained visually unchanged, with suggestion pages interleaved at relevant anchors.
- Original manuscript pages, blue editorial suggestions, and red scientific-validation warnings were inspected independently.
- The generated DOCX package passed ZIP and XML validation and rendered successfully. For PDF input, the Word copy explicitly discloses that exact editable-template recovery requires a DOCX source; the revised PDF is the template-faithful review artifact.

## Hosted evidence

- Source commit `e10b4ab` was pushed to `origin/agent/article-fit-pilot`.
- Cloud Build `d53969ae-b8ab-4d98-abdc-efa19bc6f84a` completed successfully for tag `c16-20260802-1`.
- API revision `article-fit-api-00015-joz` returned `200` from `/health` and `401` from an unauthenticated private route before receiving 100% traffic.
- Worker health execution `article-fit-worker-2gckl` completed successfully without consuming the user queue.
- The worker and retention jobs use image `c16-20260802-1`.
- Vercel preview `dpl_HCWABqUiBZ7P6QzwYhhnUGkUeZg2` was `READY`; its page declared `lang="en"`, exposed the English workflow, and returned the web health contract.
- The preview proxy authenticated to the private API and returned `Job not found` for a valid, intentionally nonexistent UUID.
- Vercel production `dpl_Acp1xMRTxagwSCvZTWxvYRVsCV7T` is `READY` and aliased to `https://article-fit.vercel.app`.
- Production returned `200` for the page and health endpoint; a cache-bypassed page check confirmed the English C16 content. The production proxy returned `Job not found` for the same non-mutating smoke check.
- One expected error log was caused by an intentionally malformed pre-verification smoke identifier; no further API error entries were recorded after the corrected validation.

## Persistence and privacy

- No new database migration, Supabase project, login, or file-retention mechanism was introduced.
- Original uploads remain temporary and are removed by the existing workflow and retention boundaries.
- Persistent journal memory continues to contain only derived journal-level conclusions.
