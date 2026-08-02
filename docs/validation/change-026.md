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
- Production dependency audit: zero vulnerabilities.

## Deployment status

Image tag: `c26-20260802-1`.

- Cloud Build `de2f01f3-aade-4128-8d83-e7e31c5d1cf1` completed successfully.
- API revision `article-fit-api-00039-jug` passed isolated health and authorization checks before receiving 100%
  of production traffic.
- Worker and retention jobs use `worker:c26-20260802-1`.
- Immediate API rollback remains `article-fit-api-00037-xiw`.

## Hosted PRL acceptance

- Project `3f2c9f63-913a-4373-ab7f-15abff0910d7`; job
  `cc085803-abca-4409-a196-211216b41194`; worker execution `article-fit-worker-kmz79`.
- The minimal-input workflow used only the journal name, three reference PDFs, and one manuscript PDF.
- Confirmed progress advanced through 0, 25, 34, 50, 56, 62, 78, 82, 84, 88, 90, 98, and 100 without
  regression. The APS publisher block no longer stopped the run at 34.
- Analysis `fa44a6d2-47f9-8239-1b8c-3905cbb295fa` reached `artifacts-ready` with 38 recommendations, 30 marked
  as scientific-impact items requiring author judgment.
- Revised manuscript DOCX: 7,223,119 bytes; OOXML ZIP integrity passed.
- Revised manuscript PDF: 630,843 bytes; 45 pages; original page retained and color-coded suggestion pages
  visually inspected.
- Revision report PDF: 288,169 bytes; 51 pages; cover, body, and final page visually inspected.
- No raw `\\frac`, `\\begin`, `\\end`, or dollar-delimited LaTeX remained in extracted artifact text.
- The project returned `documents: []` after completion. The complete QA project was then deleted and returned
  HTTP 204.
- Production API and web health checks passed; PRL resolved to ISSN `0031-9007` and the correct APS pages.
- No error-level logs were recorded for API revision `00039-jug` or worker execution `kmz79`.
