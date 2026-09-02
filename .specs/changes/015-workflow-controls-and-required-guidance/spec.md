# Change 015 — Workflow controls and required official guidance

Status: `complete`

## Objective

Give the user direct control over a running analysis, prevent progress regressions, and reduce fragile journal-discovery calls by requiring an ISSN and a complete official Scope/Guide for Authors package.

## Requirements

- Add a visible “Parar análise” action while a workflow is running.
- Cancel the durable job when it exists; otherwise abort the browser request and delete the temporary project.
- Never let overall progress or the active substep move backwards when the queued job initially reports an older milestone.
- Add a “Limpar campos” action that clears journal identity, guidance, uploads, errors, progress, and generated-result links when no workflow is running.
- Show only actionable, non-technical error guidance to the end user; retain technical detail only in private operational records and logs.
- Require journal title, ISSN, official Scope URL and text, and official Guide for Authors URL and text.
- Use the supplied title, ISSN, and same-domain official URLs to bypass external journal-identity discovery for the normal UI workflow.
- Continue to treat all submitted content as temporary and exclude it from persistent journal memory.

## Acceptance criteria

- Polling a job at 0% after the browser has reached 25% leaves the UI at 25%; later milestones can only increase it.
- Clicking “Parar análise” reaches the cancellation endpoint for a created job, stops polling and motion, and presents a calm confirmation.
- Clicking “Limpar campos” restores the initial interface and permits selecting the same files again.
- Failure text contains a useful next action and omits provider payloads, stages, HTTP codes, and internal error codes.
- Analysis cannot start without valid ISSN and the complete official guidance package.
- A complete package runs without calling OpenAlex for journal identity.
- Web, API, worker, contracts, lint, format, typecheck, build, security, preview, and production smoke checks pass.

## Files to modify

- `apps/web/src/app/page.tsx`, `page.test.tsx`, and `styles.css`.
- `apps/api/src/journal_matcher_api/main.py` and workflow tests.
- `apps/worker/src/journal_matcher_worker/main.py` and worker tests.
- Change validation, release manifest, and deployment runbook.

## Tests to run

- Monotonic 25% → queued 0% → running 25% regression.
- Job cancellation and pre-job cleanup paths.
- Reset of controlled state and native file inputs.
- Required official guidance and direct identity flow.
- Friendly error copy without technical details.
- Full local gates and hosted preview/production checks.

## Completion checklist

- [x] Owner approved Stop, Reset, simplified error guidance, and required Scope/Guide inputs.
- [x] Production evidence identified the HTTP 403 and progress-regression causes.
- [x] Implementation and automated validation complete.
- [x] CPD and hosted validation complete.
