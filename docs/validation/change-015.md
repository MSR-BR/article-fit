# Change 015 — Workflow controls and required official guidance

Status: complete.

## Production findings

- Job `01745e3f-1da3-4077-9d1b-7f60e0f06099` failed at 25% because the external journal-identity provider returned HTTP 403.
- The 25% → 0% → 25% display was a client regression: after local uploads reached 25%, the first durable-job poll still reported the initial queued milestone at 0%, and the UI replaced its newer value with the older one.

## Implemented behavior

- Overall progress and the active substep are monotonic; stale queue responses cannot move either value backwards.
- “Parar análise” cancels a created durable job. Before job creation it aborts the request and deletes the temporary project when possible.
- The worker checks the durable cancellation state between real milestones and never overwrites a cancelled job with success.
- “Limpar campos” clears journal identity, official guidance, uploads, progress, errors, and artifact links, and remounts file inputs so the same files can be selected again.
- User-facing errors contain only a useful next action. Provider payloads, HTTP status, stage, and internal codes remain private operational evidence.
- Journal title, ISSN, official Scope URL/text, and official Guide for Authors URL/text are required.
- Valid supplied identity and same-domain HTTPS guidance URLs bypass OpenAlex journal discovery in the normal UI flow.

## Automated evidence

- Web: 19 tests passed with 94.76% statement coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 108 tests passed with 90.35% total coverage.
- Total: 133 tests passed.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, production dependency audit, and diff checks passed.

## Hosted evidence

- Source implementation commit: `a6a7492` on `agent/article-fit-pilot`.
- Cloud Build `53c173a8-2ba3-422e-a3b8-61922b1cc3c3` completed successfully for tag `c15-20260802-1`.
- API revision `article-fit-api-00013-jab` passed health and private-route checks before receiving 100% traffic.
- Worker health execution `article-fit-worker-78bbg` completed successfully without consuming the user queue.
- The worker and retention jobs use image `c15-20260802-1`.
- Vercel preview `dpl_96Ujy4oCKon4KcTaEfUMLdJ3K5nD` was `READY` before promotion.
- Vercel production `dpl_BiS1knvg31GMHrnC38LhT1GCXs7Z` is `READY` and aliased to `https://article-fit.vercel.app`.
- Browser verification found all six required fields, the Reset action, a correctly disabled initial Analyze action, no framework overlay, and no console errors.
- The production proxy reached the private API and returned `Job not found` for an intentionally nonexistent resource.
- No Vercel or C15 API error entries were found in the post-deploy window.

## Persistence and privacy

- No database migration or additional Supabase project was needed.
- Official guidance text remains part of the temporary project evidence and is removed under the existing source-document and 24-hour retention boundaries.
- Persistent journal memory continues to contain only derived journal-level conclusions.
