# Change 019 — Resilient journal memory and artifact feedback

Status: deployed and production health verified.

## Production incident diagnosis

- Failed job: `92bce2fc-241e-490a-b11f-bc461362a828` in Cloud Run execution `article-fit-worker-2rnbv`.
- The worker continued independently of the browser from 18:21 to 18:27 UTC, so computer sleep was not the cause.
- Attempt zero reached the `ai-review` stage at 78% and rejected three Gemini anchors longer than the 200-character contract.
- Platform retries one and two then encountered a temporary Gemini connection failure and HTTP 503.
- The terminal error therefore came from recoverable provider output/availability, not missing inputs or a sleeping local computer.

## Corrected behavior

- Gemini length limits are represented in the provider schema and bounded length-only drift is normalized before semantic validation.
- Transient HTTP 429 and 5xx responses receive three bounded attempts inside one worker execution.
- A structurally valid but incomplete review receives one full replacement pass and must then satisfy all scientific/editorial dimensions.
- Browser polling retries temporary network loss for up to one minute, keeps confirmed progress monotonic, and explains that the server is still processing.
- Before manuscript review, Gemini refines the current journal memory from bounded reference-article evidence; the resulting profile version is used immediately by the same analysis.
- Existing and new conclusions are merged in one append-only profile per ISSN. `optimizationCount` is the immutable version number and `feedbackCount` reports applied feedback lessons.
- Each output card contains independent feedback controls.
- Feedback is treated as untrusted data. Raw comments are never persisted; only a one-way hash, a generic evidence record, and a derived advisory lesson may enter journal memory.
- Feedback-derived lessons cannot be official requirements or verified journal facts.

## Supabase and privacy validation

- No database migration or second Supabase project is required; the existing `journal_profile_versions` and `journal_profile_heads` tables implement the shared standard.
- Existing tables remain RLS-enabled and closed to `anon` and `authenticated`; only the server-side service role reaches them.
- Uploaded files, filenames, manuscript text, reference text, and raw feedback remain absent from durable profile payloads.
- Supabase's current RLS guidance and 2026 changelog were reviewed. No current breaking change affects this server-side PostgREST path.

## Automated evidence

- Web: 22 tests passed with 93.05% statement coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 119 tests passed with 90.04% total coverage.
- Total: 147 tests passed.
- Formatting, lint, typecheck, production build, dependency boundaries, and secret scan passed.
- Production dependency audit reported zero vulnerabilities.

## Visual evidence

- Vercel preview `dpl_EHnPiryiRu1Ao84i5a3822PkkhA7` built successfully and reached `READY`.
- The protected preview redirected the anonymous validation browser to Vercel login as expected.
- The same build was rendered locally in a real browser. The minimal layout, required guidance inputs, primary actions, and responsive single-column presentation were visually inspected without regression.
- Artifact-specific feedback controls are conditionally rendered only after successful output generation and are covered by component interaction tests.

## Hosted evidence

- Source commit `9c76c9e` was pushed to `origin/agent/article-fit-pilot`.
- Cloud Build `9da59313-6546-4b21-ac4c-d5d08492569e` completed successfully for tag `c19-20260802-1`.
- API revision `article-fit-api-00021-yul` returned 200 from `/health` and 401 from an unauthenticated private resource before receiving traffic.
- The API revision now receives 100% traffic; C18 revision `article-fit-api-00019-sep` remains available at 0% for rollback.
- Worker and retention jobs use the C19 image. Worker execution `article-fit-worker-9npbb` completed with `processed=0` and `failures=0`.
- Vercel production `dpl_DFFhcQM4d1wGSkrk2LDFgcHFKZ6C` reached `READY` and owns `https://article-fit.vercel.app`.
- The public page and frontend health returned 200. A versioned proxy request reached the backend through the dynamic Vercel route and returned the expected JSON 404 for a nonexistent project.
- The public production interface was opened, snapshotted, and visually inspected in a real browser.
- No error logs were found for the promoted Vercel deployment or Cloud Run revision.
