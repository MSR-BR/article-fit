# Change 026 — Official-guidance memory fallback

## Objective

Prevent a publisher access block from stopping an analysis when Article Fit already has validated official guidance for the resolved journal.

## Requirements

- Search the journal's immutable profile history for the newest retained scope and author-guide snapshots.
- Reuse those snapshots when the current publisher request is blocked or temporarily unavailable.
- Carry official snapshots forward when feedback or another memory-only update creates a new profile version.
- Surface an English, user-oriented verification warning without exposing provider or HTTP internals.
- Keep the first analysis for an unknown journal fail-closed when neither current official guidance nor validated memory exists.

## Acceptance criteria

- A PRL run with an APS HTTP 403 and historical PRL snapshots proceeds beyond official guidance.
- The research result identifies reused sources as `cached-official` and includes a time-sensitive-guidance warning.
- A feedback-only profile version retains both official snapshots.
- Existing assisted-capture and fresh-page paths continue to work.
- A hosted production run reaches deliverable generation with the publisher-block condition reproduced.

## Files to modify

- `apps/api/src/journal_matcher_api/main.py`
- `apps/api/src/journal_matcher_api/journal_research.py`
- `apps/api/src/journal_matcher_api/hosted.py`
- API repository and integration tests
- Validation and deployment documentation

## Tests to run

- Targeted journal-research and hosted-repository tests
- Full Python test suite with coverage
- Web tests, lint, typecheck, build, boundaries, secrets, and dependency audit
- Hosted PRL end-to-end execution with an actual publisher access block

## Completion checklist

- [x] Historical fallback implemented.
- [x] Snapshot inheritance implemented.
- [x] Regression tests passed.
- [ ] Hosted PRL execution passed.
- [ ] CPD complete.
