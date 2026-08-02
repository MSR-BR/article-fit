# Change 017 — Idempotent analysis persistence

## Objective

Prevent repeated journal analyses from failing at the manuscript-comparison stage when reusable journal rules or recommendations have identities previously stored by another analysis.

## Requirements

- Guide-rule and recommendation identities must be deterministic and scoped to their analysis.
- Reusing the same journal profile in a new project must not create primary-key collisions with a prior analysis.
- Hosted analysis creation must be idempotent and must repair an existing partial analysis by inserting any missing child records.
- Safe workflow retries must ignore already inserted child records without detaching them from the current analysis.
- AI-generated recommendation identities must follow the same analysis-scoping rule.
- The public error message for a post-research persistence conflict must not incorrectly blame missing fields or documents.
- Internal error details must remain hidden from the user.
- No database migration or new Supabase project may be introduced for this fix.

## Acceptance criteria

- Two analyses may derive the same base journal rule without sharing the stored child identity.
- Retrying creation for an existing analysis inserts missing rules and recommendations.
- Child inserts use idempotent conflict handling and remain attached to the correct analysis.
- Recommendation decisions continue to reference the public recommendation identity returned by the analysis API.
- A failed job at or after journal research displays an actionable reset-and-retry message rather than a missing-input message.
- Unit, integration, web, lint, type, build, boundary, and secret gates pass.
- A hosted smoke workflow progresses beyond the 62% manuscript-analysis milestone.

## Files to modify

- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- `apps/api/src/journal_matcher_api/hosted.py`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/page.test.tsx`
- `tests/unit/test_hosted_repositories.py`
- Change 017 validation and release evidence

## Tests to run

- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run check:boundaries`
- `npm run check:secrets`
- Production health, proxy, worker-health, and workflow-stage smoke checks

## Completion checklist

- [x] Root cause confirmed from production worker logs and partial-analysis state.
- [x] Analysis-scoped child identities implemented.
- [x] Partial hosted analyses are repaired idempotently.
- [x] Post-research conflict copy corrected.
- [x] Regression tests added.
- [x] Automated gates pass.
- [ ] Commit, push, deployment, and hosted verification complete.
