# Change 018 — Scientific review and equation-safe documents

Status: deployed and production health verified.

## Corrected behavior

- The progress dialog closes automatically after the server confirms that the artifact set is ready; output links remain visible.
- Gemini receives bounded beginning/middle/end excerpts from each uploaded reference article, together with official rules, journal-profile claims, deterministic checks, and manuscript segments.
- The structured Gemini contract requires at least 12 executable proposals spanning scientific framing, theory/methodology, validation/robustness, results/analysis, figures/equations, structure, writing, and compliance.
- A review missing any required dimension is rejected instead of being exported as a superficial report.
- Every substantive proposal distinguishes journal expectation, observed reference pattern, manuscript diagnosis, author action, and optional proposed wording.
- New analyses, measurements, figures, or validation are presented as author tasks; unknown results are never invented.
- PDF-source Word reviews preserve each source page visually and interleave blue Article Fit suggestion pages. DOCX-source reviews retain the original package and add color-coded suggestions.
- Mathematical suggestions are rendered as equation images in Word and as embedded mathematical images in generated PDF reports. Raw LaTeX control strings are not printed as final equations.

## Artifact and visual validation

- A two-page sample derived from the supplied physics manuscript was used for artifact QA.
- Every rendered page of the six-page Word review, ten-page report PDF, and eight-page revised PDF was inspected in contact sheets.
- Original two-column manuscript pages remained visually intact.
- Suggested text appeared in blue, scientific-validation warnings in red, and original pages retained their source appearance.
- A representative equation rendered with fractions, angle brackets, Greek symbols, and subscripts in both Word and PDF.

## Automated evidence

- Web: 20 tests passed; 94.71% statement coverage and 82.58% branch coverage.
- Shared contracts: 6 tests passed with 100% coverage.
- Python API/worker: 113 tests passed with 90.47% total coverage.
- Total: 139 tests passed.
- Formatting, lint, typecheck, production build, dependency boundaries, secret scan, and production dependency audit passed.
- Production dependency audit reported zero vulnerabilities.

## Hosted evidence

- Source commit `7821e0c` was pushed to `origin/agent/article-fit-pilot`.
- Cloud Build `4ca7c56a-c17c-4f37-97b2-415ea33b5162` completed successfully for tag `c18-20260802-1`.
- API revision `article-fit-api-00019-sep` returned `200` from `/health` and `401` from an unauthenticated private resource before receiving 100% traffic.
- Worker and retention jobs use the C18 image; worker health execution `article-fit-worker-ps9r9` completed successfully.
- Vercel preview `dpl_4NgNJPnVydP8v9rse56A3T8pFDbY` passed web health and authenticated proxy checks.
- Vercel production `dpl_CMugbTY5h1u1kjAVfU4YRCJdJun8` is `READY` and owns the `https://article-fit.vercel.app` aliases.
- Production web health, API health, and authenticated proxy checks passed.
- No error entries were found for the promoted API revision.

## Operational note

The next owner run should use the same manuscript and references to evaluate the scientific usefulness of the new Gemini review. That expert judgment remains an internal validation activity rather than an automated acceptance claim.
