# Change 020 — Provider resilience

## Objective

Prevent external AI or research-provider failures from destroying an otherwise valid analysis, and make every degraded path explicit, bounded, observable, and retryable.

## Requirements

- Use a stable Gemini model by default and allow an explicit fallback model.
- Retry transient failures with bounded backoff.
- If Gemini rejects a complex response schema with HTTP 400, retry the same task with JSON-only output and local validation.
- Log a sanitized provider reason and stage without prompts, keys, uploaded text, or filenames.
- Journal-memory synthesis failure must retain the previous/deterministic memory and continue.
- Editorial AI failure must preserve deterministic results and still produce clearly limited deliverables.
- Worker retries must resume idempotently without duplicating analyses or artifacts.

## Acceptance criteria

- The production HTTP 400 at 56% no longer terminates the workflow.
- Schema fallback and stable-model fallback are unit tested.
- Memory degradation is visible in the report but not presented as journal evidence.
- No private input appears in logs.

## Files to modify

- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/main.py`
- `apps/worker/src/journal_matcher_worker/main.py`
- Relevant tests and operational documentation

## Tests to run

- Gemini HTTP 400 schema-fallback tests
- Memory and editorial degradation integration tests
- Worker idempotency and terminal-state tests

## Completion checklist

- [x] Stable model and fallback implemented.
- [x] Schema rejection fallback implemented.
- [x] Memory/editorial degradation implemented.
- [ ] Tests and production validation passed.
