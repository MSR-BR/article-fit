# Change 026 validation — official-guidance memory fallback

Date: 2026-08-02

## Incident evidence

- Production job: `b1bde0da-1073-4160-afbf-c261cf8b1f03`.
- The journal resolved correctly to Physical Review Letters, ISSN `0031-9007`, on `journals.aps.org`.
- The worker stopped at `official-guidance`, progress 34, after APS returned HTTP 403.
- The PRL memory head was version 20 and contained seven durable evidence records, including four official-source
  records, but no raw official snapshot rows.
- Older PRL memory versions retained both official snapshots. Feedback-only memory updates had advanced the head
  without copying those snapshots forward.

## Correction

- Official-page fallback now searches the immutable journal history and chooses the newest retained scope and
  guide snapshots.
- Cached official text is labelled `cached-official` and produces an English warning to verify time-sensitive
  submission requirements.
- New feedback-only or memory-only versions inherit both official snapshots, preventing the head from losing its
  executable evidence.
- A journal with neither accessible official pages nor validated historical snapshots still fails closed and
  asks for assisted official guidance.

## Automated validation

- Targeted API/repository regression tests: 35 passed.
- Full Python suite: 135 passed; total coverage 90.36%.
- Web suite: 23 passed; statement coverage 93.34%.
- Lint, typecheck, production build, format check, dependency boundaries, and secret scan passed.
- The online npm audit could not be repeated because the Codex environment denied external execution after its
  usage quota was reached. Dependencies were unchanged; the immediately preceding C25 audit reported zero
  vulnerabilities.

## Deployment status

Image tag reserved: `c26-20260802-1`.

Cloud Build submission was attempted only after all local gates passed. The Codex environment blocked outbound
execution because its external-tool usage quota was exhausted. No C26 image, Cloud Run revision, worker update,
production promotion, or hosted PRL execution has therefore occurred. Production remains on
`article-fit-api-00037-xiw` / `c25-20260802-9` until the pending release steps can be executed safely.
