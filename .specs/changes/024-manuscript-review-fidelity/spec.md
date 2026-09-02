# Change 024 — Manuscript review fidelity

## Objective

Deliver a manuscript review that preserves the original document and makes every proposed intervention immediately understandable.

## Requirements

- Original content remains black and unchanged.
- Suggested wording/actions use category color, labels, anchors, and author-validation warnings.
- DOCX input preserves the original package/template and inserts anchored review blocks.
- PDF input preserves every original page and interleaves clearly labeled suggestion pages.
- LaTeX suggestions are rendered as equations in DOCX and PDF.
- DOCX and PDF contain the same visible proposal set.

## Acceptance criteria

- Original page count/content is preserved in the PDF review copy.
- Anchored suggestions include diagnosis, action, and proposed text where available.
- Proposal parity and scientific-invariant validation pass.

## Files to modify

- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- `apps/api/src/journal_matcher_api/artifact_rendering.py`
- Artifact tests

## Tests to run

- DOCX package-preservation test
- PDF page-preservation test
- Equation rendering and proposal-parity tests

## Completion checklist

- [x] DOCX review blocks improved.
- [x] PDF review pages improved.
- [x] Equations render.
- [x] Parity tests passed.
