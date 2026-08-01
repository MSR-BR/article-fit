# Change 007 — Integrate Research Starter and Strengthen Final Review Products

Status: `complete`

## Objective

Use Research Starter as a server-side literature-discovery adapter while preserving Journal Matcher as the authority for journal identity, lawful full-text acquisition, editorial-pattern extraction, manuscript comparison, and final DOCX/PDF products.

## Requirements

- Call `POST /api/v1/reports` only from the backend with a Bearer key stored outside Git.
- Require `apiVersion=v1`; record `contractVersion`, coverage, warnings, AI disclosure, and source-rights summary.
- Treat returned papers as candidates, not verified same-journal evidence; independently validate ISSN, DOI, dates, identity, and lawful open access.
- Continue when Research Starter is unavailable or returns fewer than three usable candidates.
- Build the journal pattern from measurable writing and presentation characteristics of the supplied and lawfully acquired full texts, not from similarity of their physics topics.
- Compare the manuscript with the observed sample and official instructions, keeping official requirements, observed patterns, and expert questions separate.
- Produce an evidence-backed revision report plus annotated/reconstructed DOCX and PDF review copies.
- Never apply scientific-meaning changes without explicit author-modified text.

## Acceptance criteria

- Secrets are never returned, logged, committed, or sent to the browser.
- Contract errors, timeouts, 401, 502, partial coverage, and unknown additive response fields are handled safely.
- Research Starter failure is a warning rather than a project blocker.
- Every article used for the editorial pattern has verified journal identity and sufficient lawful full text.
- Pattern claims report the actual sample size and coverage.
- Final report covers official compliance, observed editorial deviations, architecture, language, presentation, scientific questions, author actions, sources, and limitations.
- DOCX/PDF outputs are structurally and visually validated before delivery.

## Files to modify

- `.specs/changes/007-integrate-research-starter/spec.md`
- `apps/api/src/journal_matcher_api/research_starter.py`
- `apps/api/src/journal_matcher_api/main.py`
- `apps/api/src/journal_matcher_api/journal_research.py`
- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- tests, environment examples, and validation documentation
- `scripts/generate-validation-products.py`

## Tests to run

- Adapter authentication, request, response, timeout, partial-response, and redaction tests.
- Same-journal verification and insufficient-extra-article tests.
- Editorial-pattern metric and manuscript-deviation tests.
- Full lint, formatting, strict typing, unit/integration tests, artifact validation, DOCX render QA, and PDF render QA.

## Completion checklist

- [x] Contract and credentials received outside Git.
- [x] Backend adapter implemented and tested.
- [x] Editorial-pattern analysis upgraded.
- [x] Final report and manuscript review products upgraded.
- [x] Real PRL case regenerated and visually validated.
