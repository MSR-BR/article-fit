# Change 022 — Manuscript literature and scope audit

## Objective

Evaluate the manuscript's scientific and academic positioning against its own bibliography, recent literature, the official journal Scope, and the journal's level of substantiation.

## Requirements

- Extract the manuscript title, abstract, bibliography entries, DOIs, arXiv identifiers, and publication-year signals.
- Use Research Starter to obtain a recent literature landscape from manuscript-derived topic terms.
- Treat Research Starter results as candidate literature until validated and label limitations.
- Give Gemini only bounded, source-identified literature and official-scope evidence.
- Require scope-fit, literature-positioning, novelty/significance, methods, validation, results, figures/equations, structure, writing, and compliance coverage.
- Never invent a citation, novelty claim, experiment, calculation, or result.

## Acceptance criteria

- The final report discusses scope fit, bibliography coverage, close/recent work, novelty risk, safe claims, claims to avoid, and concrete scientific upgrades.
- Literature recommendations cite human-readable source labels.
- Missing verification is shown as an author action, not filled with invented content.

## Files to modify

- New `apps/api/src/journal_matcher_api/literature_audit.py`
- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/main.py`
- Literature, Gemini, and integration tests

## Tests to run

- Bibliography extraction tests
- Prompt evidence-boundary tests
- Research Starter degradation tests
- Scientific coverage tests

## Completion checklist

- [x] Bibliography extraction implemented.
- [x] Recent-literature integration implemented.
- [x] Scope/novelty categories enforced.
- [x] Tests passed.
