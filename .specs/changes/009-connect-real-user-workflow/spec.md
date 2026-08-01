# Change 009 — Connect the Real User Workflow

Status: `complete`

## Objective

Connect the minimal upload interface to the real backend while preserving explicit user identification of the target journal and presenting truthful, stage-based progress and downloadable outputs.

## Requirements

- Treat the journal title, ISSN, or official URL entered by the user as the journal candidate; never infer the journal from uploaded reference PDFs.
- Resolve candidate metadata into a title, ISSN, official domain, official scope URL, and official author-guide URL using attributable external evidence.
- Require a unique, sufficiently confident match. Stop with a clear correction request when the candidate is ambiguous or official pages cannot be verified.
- Never manufacture ISSNs, domains, URLs, source content, or completion states.
- Upload exactly the manuscript and the first three validated orientation PDFs supported by the MVP API; report that extra files are retained for a later multi-reference extension rather than silently discarding them.
- Execute ingestion, journal research, deterministic analysis, Gemini editorial review, and artifact generation through server-side orchestration.
- Derive each progress state from a completed backend operation. No timers may simulate work.
- Show recoverable errors, allow retry, and preserve the selected local files when safe.
- Display actual downloadable DOCX/PDF artifacts only after successful generation.
- Keep credentials and provider configuration server-side.

## Acceptance criteria

- A supported journal candidate can be resolved and explicitly displayed before analysis proceeds.
- The visible stages correspond to real API state transitions.
- A successful run produces working report and revised-manuscript download controls.
- Ambiguous journal identity, missing official guidance, provider outage, malformed upload, Gemini failure, and artifact failure produce truthful actionable errors.
- Tests prove that no synthetic timer can advance progress and no result card appears before artifacts exist.

## Files to modify

- `apps/api/src/journal_matcher_api/main.py`
- `apps/api/src/journal_matcher_api/journal_resolution.py`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/styles.css`
- API and web tests
- Shared contracts and environment examples when required

## Tests to run

- Journal resolution matching, ambiguity, official-domain validation, and provider failure tests.
- Backend orchestration success, retry, authorization, and partial-failure tests.
- Frontend API mocking, real stage transitions, errors, accessibility, and artifact-download tests.
- Full lint, typing, unit/integration test, coverage, build, and secret scans.

## Completion checklist

- [x] Evidence-backed journal resolver implemented (identity plus same-domain official scope/guide discovery).
- [x] Server-side orchestration endpoint implemented and covered by an end-to-end mocked-provider test.
- [x] UI connected without simulated progress.
- [x] Real artifact downloads displayed.
- [x] Failure and retry paths validated.
- [x] Full automated quality gates pass.

## Verified protected-publisher behavior

- The real PRL/OpenAlex identity lookup succeeds after safely upgrading its legacy HTTP homepage metadata to HTTPS.
- APS protects the journal pages with a Cloudflare challenge and its `robots.txt` disallows automated collection for the Journal Matcher user agent. The app does not bypass the publisher restriction.
- A user-supplied assisted-capture fallback is implemented. It requires both official same-domain URLs and at least 500 characters copied from each visible official page; the evidence is stored as browser-assisted and auditable.
