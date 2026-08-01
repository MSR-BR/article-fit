# Decision 0002 — Change 004 scope readiness

Status: accepted

## Context

Change 004 combines the highest-risk product behavior: interpreting official rules, evaluating a scientific manuscript, proposing edits, collecting author decisions, and generating DOCX/PDF/report artifacts. The original draft did not define the supported document matrix, the authority allowed for each recommendation class, behavior without a model provider, or the boundary with Changes 005 and 006.

Change 003 provides immutable official-page snapshots and evidence-backed structural/style observations. It does not yet extract detailed author-guide rules, so Change 004 must perform that transformation and provenance validation before checking compliance.

## Proposed decision

- Keep artifact generation in Change 004; reserve Change 006 for deployment and operational download controls.
- Implement DOCX as the full-fidelity editable path and label PDF reconstruction limitations prominently.
- Keep the model boundary provider-neutral. Deterministic analysis must remain useful when no model is configured; qualitative analysis degrades explicitly.
- Treat scientific-content edits as review-required proposals and never apply them automatically.
- Store recommendations and decisions append-only so every output is reproducible from immutable inputs and versions.
- Complete automated/golden validation in Change 004 and reserve blind expert sign-off and release thresholds for Change 005.

## Consequences

- A production model vendor, data-processing agreement, retention setting, region, and cost budget remain a blocking decision before enabling real qualitative analysis outside synthetic fixtures.
- The first supported document matrix is intentionally narrower than arbitrary Word/PDF documents.
- Guide-rule extraction becomes an explicit C4 stage rather than an undocumented prerequisite.
