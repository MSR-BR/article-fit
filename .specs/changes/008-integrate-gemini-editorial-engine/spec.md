# Change 008 — Integrate Gemini Editorial Engine

Status: `complete`

## Objective

Add a server-side Gemini adapter that converts evidence-backed manuscript comparisons into structured editorial proposals without exposing credentials, inventing sources, or silently changing scientific meaning.

## Requirements

- Read `GEMINI_API_KEY` only on the server and transmit it only in the `x-goog-api-key` header.
- Keep the model configurable through `GEMINI_MODEL` and record the selected model with every run.
- Request structured JSON, validate its schema locally, and reject malformed or unsupported values.
- Separate official requirements, observed journal patterns, and expert suggestions.
- Require source identifiers for evidence-backed proposals and mark scientific-impact changes for author validation.
- Never log the API key, raw private manuscript, or complete model request.
- Use mocked tests by default; a real paid request requires an explicit bounded validation step.

## Acceptance criteria

- The key is absent from browser bundles, API responses, logs, Git, and exception messages.
- Valid structured responses become typed editorial proposals.
- Invalid evidence references and unsafe scientific changes are rejected.
- Provider errors are normalized without leaking request content or credentials.
- Deterministic checks remain available when Gemini is unavailable.

## Files to modify

- `.specs/changes/008-integrate-gemini-editorial-engine/spec.md`
- `.env.example`
- `apps/api/src/journal_matcher_api/gemini.py`
- `apps/api/src/journal_matcher_api/main.py`
- `apps/api/src/journal_matcher_api/manuscript_analysis.py`
- `tests/unit/test_gemini.py`
- `tests/integration/test_manuscript_analysis_flow.py`
- `scripts/validate_gemini_connection.py`

## Tests to run

- Authentication header, secret redaction, structured parsing, semantic validation, provider failure, lint, typing, and full tests.

## Completion checklist

- [x] Local key presence confirmed without disclosure.
- [x] Server-side adapter and mocked contract tests implemented.
- [x] Editorial prompt assembled from bounded evidence packages.
- [x] Gemini proposals integrated with deterministic recommendations.
- [x] One bounded real-provider validation approved and recorded (`gemini-3.5-flash`, one proposal, no private input).
- [x] Gemini integration contract is ready for backend orchestration; UI orchestration is assigned to Change 009.
