# Change 018 — Scientific review and equation-safe documents

## Objective

Make the final deliverables scientifically useful and visually readable: a reference-informed editorial report, a template-faithful color-coded manuscript review, correctly rendered mathematical expressions, and a progress dialog that closes automatically after success.

## Requirements

- The progress dialog must close automatically only after the server confirms that all deliverables are ready.
- Gemini must receive bounded excerpts from the uploaded reference articles in addition to the derived journal profile.
- The AI review must cover scientific framing, argument architecture, methods and assumptions, validation and robustness, results and interpretation, figures/equations, structural cuts or moves, writing, and compliance.
- Proposed new analyses, measurements, controls, or validation steps must be explicit author actions and must never be presented as completed results.
- Provider output that lacks the required scientific/editorial dimensions must be rejected instead of producing a superficial report.
- The report must distinguish the current manuscript, the observed journal/reference pattern, the diagnosis, the concrete author action, and optional proposed wording.
- LaTeX-like expressions in suggestions must be rendered as mathematical notation rather than printed as raw commands.
- For a PDF manuscript, the revised Word document must preserve each original source page visually and interleave color-coded Article Fit suggestions; it must not reconstruct the manuscript as plain text.
- For a DOCX manuscript, the original package, formatting, and equations must remain intact while suggestions are added in another color.
- Uploaded source documents remain ephemeral and are not added to journal memory.

## Acceptance criteria

- A successful run leaves the output links visible and no progress dialog open.
- The Gemini evidence package contains bounded reference-article excerpts and does not expose them as reusable journal memory.
- Structured AI output requires substantive coverage of all major scientific/editorial dimensions.
- A PDF-source revised DOCX visibly contains the original source pages plus blue suggestion pages/cards.
- Mathematical expressions in generated suggestion content are rendered or presented in a readable mathematical form without raw LaTeX control sequences.
- The report includes concrete scientific-content, structural, reduction, validation, results-analysis, and presentation recommendations, each with evidence boundaries and author-validation flags.
- Unit, integration, web, lint, type, build, boundary, secret, artifact, and visual checks pass.
- Commit, push, and production deployments complete successfully.

## Files to modify

- `.specs/changes/018-scientific-review-and-equation-safe-documents/spec.md`
- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/main.py`
- `apps/api/src/journal_matcher_api/artifact_rendering.py`
- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- `apps/api/Dockerfile`
- `apps/worker/Dockerfile`
- `pyproject.toml`
- `requirements.lock`
- `apps/web/src/app/page.tsx`
- Relevant unit, integration, and web tests

## Tests to run

- Focused Gemini, manuscript-artifact, integration, and web tests
- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run check:boundaries`
- `npm run check:secrets`
- Render and visually inspect representative revised DOCX and PDF artifacts
- Production API, worker, proxy, and artifact smoke checks

## Completion checklist

- [x] Reference excerpts included in the bounded Gemini review context.
- [x] Scientific/editorial coverage contract implemented and validated.
- [x] Report content hierarchy upgraded.
- [x] PDF-source Word review preserves the visual manuscript.
- [x] Mathematical expressions render legibly.
- [x] Progress dialog closes after success.
- [x] Automated and visual checks pass.
- [x] Commit, push, deployment, and production verification complete.
