# Change 021 — Minimal intake

## Objective

Reduce the normal user input to the target journal name, reference PDFs, and manuscript while retaining a safe manual recovery path.

## Requirements

- Journal name remains required because uploaded reference files may be arXiv copies without journal branding.
- ISSN, Scope URL, and Guide for Authors URL are not required in the normal flow.
- The backend resolves the journal, ISSN, official Scope, and official Guide automatically.
- Optional manual identity/guidance fields stay collapsed and are explained as recovery-only.
- Manual snapshots are not requested in the primary interface.

## Acceptance criteria

- A user can start with only the journal name, three reference PDFs, and one manuscript.
- Automatic discovery produces the same verified identity contract used downstream.
- Partial optional guidance is rejected with a useful recovery instruction.

## Files to modify

- `apps/web/src/app/page.tsx`
- `apps/web/src/app/styles.css`
- `apps/api/src/journal_matcher_api/main.py`
- Journal-resolution and web tests

## Tests to run

- Minimal-input component test
- Automatic journal-resolution integration test
- Optional manual-recovery validation tests

## Completion checklist

- [x] Primary form simplified.
- [x] Automatic discovery path verified.
- [x] Manual recovery remains available but unobtrusive.
- [x] Tests passed.
