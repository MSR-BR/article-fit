# Change 019 — Resilient journal memory and artifact feedback

## Objective

Make the hosted workflow resilient to temporary AI-provider and browser-connection failures, explicitly evolve one shared journal standard per ISSN on every completed evidence cycle, and let users submit artifact-specific feedback that becomes bounded, reusable journal-memory guidance.

## Requirements

- A sleeping or temporarily disconnected browser must not stop the Cloud Run worker.
- Temporary polling failures must be retried without resetting confirmed progress or falsely marking the analysis as failed.
- Gemini HTTP 429 and transient 5xx responses must use bounded retries.
- Safely repair bounded provider-format defects, such as an overlong anchor, before rejecting an otherwise valid structured review.
- If a first AI review is structurally valid but misses required scientific/editorial dimensions, request one complete repair pass and validate it again.
- The existing append-only `journal_profile_versions` history remains the single journal memory; no uploaded files or raw private text may be added to it.
- Each journal research cycle must merge previous memory with new official and article-derived evidence before manuscript review.
- Gemini must synthesize reusable editorial patterns from bounded new article evidence and the previous memory before the current manuscript review begins.
- Every returned journal profile must expose its version as `optimizationCount` and count applied feedback cycles.
- Each generated artifact must have its own feedback field and submission status.
- Artifact feedback must be treated as untrusted input, analyzed by Gemini, and converted only into a bounded advisory lesson.
- Raw feedback text must not be stored in journal memory. Only a one-way hash, a generic source record, and the derived advisory lesson may persist.
- Feedback-derived guidance must never be represented as an official requirement or verified journal fact.
- The public browser must continue to use only the server proxy; Supabase service credentials remain server-side.

## Acceptance criteria

- The production failure at 78% caused by overlong Gemini anchors no longer fails validation.
- Temporary Gemini 503 responses are retried within the worker before a terminal failure is reported.
- Confirmed progress is monotonic through transient browser disconnections.
- A journal profile response includes `optimizationCount`, `feedbackCount`, and `supersedesId`.
- A later analysis for the same ISSN starts from the current memory head and publishes a new merged version before the manuscript AI review.
- The new merged version contains AI-synthesized, evidence-cited editorial patterns and is the exact profile consumed by the current manuscript review.
- Each of the three output cards includes an independent feedback textarea and submit button.
- Submitting actionable feedback verifies the artifact, invokes bounded AI analysis, publishes a new journal-memory version, and returns the new optimization count.
- Stored profile evidence contains no raw feedback, uploaded bytes, filenames, manuscript text, or reference-article text.
- Non-actionable feedback is acknowledged without corrupting journal memory.
- Unit, integration, web, lint, type, build, boundary, secret, and production smoke checks pass.

## Files to modify

- `.specs/changes/019-resilient-journal-memory-and-artifact-feedback/spec.md`
- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/journal_research.py`
- `apps/api/src/journal_matcher_api/hosted.py`
- `apps/api/src/journal_matcher_api/main.py`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/styles.css`
- Relevant API, repository, integration, and web tests
- Change validation and release documentation

## Tests to run

- Focused Gemini normalization/retry/repair tests
- Journal-memory version and privacy tests
- Artifact-feedback API tests for actionable, non-actionable, invalid, and provider-error cases
- Web tests for independent feedback forms and monotonic reconnect behavior
- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run check:boundaries`
- `npm run check:secrets`
- Preview deployment, production promotion, Cloud Run worker health execution, and production smoke checks

## Completion checklist

- [x] Root cause confirmed from production logs.
- [x] Gemini normalization, retry, and coverage-repair path implemented.
- [x] Browser polling tolerates temporary disconnection without progress regression.
- [x] Journal optimization and feedback counters exposed.
- [x] AI synthesis refines journal memory before the current manuscript review.
- [x] Artifact-specific feedback UI and API implemented.
- [x] Feedback learning remains advisory, provenance-bounded, and free of raw private text.
- [x] Automated and production checks pass.
- [x] Commit, push, and production deployments complete.
