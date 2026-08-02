# Change 025 — End-to-end release gate

## Objective

Prove the hosted workflow completes from minimal input to all three downloadable artifacts before production promotion.

## Requirements

- Add structured stage/provider observability without private payloads.
- Test browser progress, cancellation, reconnection, completion, downloads, and feedback.
- Run an actual hosted worker execution and inspect API/worker/Vercel error logs.
- Render and inspect generated PDF pages.
- Commit, push, deploy, smoke test, and retain a rollback revision.

## Acceptance criteria

- A production-like run reaches 100% and all artifacts pass structural and visual checks.
- Public frontend and versioned backend proxy respond as expected.
- No new error logs appear after promotion.

## Files to modify

- Web/API/worker tests
- `docs/validation/change-025.md`
- Release and operations documentation

## Tests to run

- Full Python and web test suites with coverage
- Lint, typecheck, build, boundaries, secrets, dependency audit
- Hosted execution and production smoke test

## Completion checklist

- [ ] Automated gates passed.
- [ ] Hosted end-to-end execution passed.
- [ ] Visual artifact QA passed.
- [ ] CPD complete.

