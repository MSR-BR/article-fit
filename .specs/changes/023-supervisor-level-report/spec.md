# Change 023 — Supervisor-level report

## Objective

Produce a readable academic assessment comparable in structure and usefulness to the supplied PRL viability and novelty report.

## Requirements

- Use a formal cover, contents overview, numbered sections, running headers, page numbers, readable tables, equations, and references.
- Include executive verdict, evidence boundary, scope fit, literature/novelty positioning, direct journal-pattern comparison, scientific upgrades, recommended manuscript architecture, title/abstract/significance options, figure plan, staged action plan, journal strategy, detailed ledger, and final recommendation.
- Distinguish requirements, observed patterns, literature candidates, and expert suggestions.
- Render LaTeX expressions instead of exposing raw control sequences.
- Include human-readable source titles/identifiers.

## Acceptance criteria

- Rendered pages contain no clipped, overlapping, raw-LaTeX, or illegible text.
- The report contains substantive scientific/structural actions, not only surface edits.
- A benchmark test rejects reports missing core model sections.

## Files to modify

- `apps/api/src/journal_matcher_api/artifact_rendering.py`
- `apps/api/src/journal_matcher_api/main.py`
- Artifact and benchmark tests

## Tests to run

- PDF structural and text-content tests
- Rendered-page visual inspection
- Model-section benchmark

## Completion checklist

- [x] Report structure rebuilt.
- [x] Equations and references render correctly.
- [x] Visual QA passed.
- [x] Benchmark passed.
