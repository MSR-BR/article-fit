# Change 025 validation — end-to-end release gate

Date: 2026-08-02

Production frontend: `https://article-fit.vercel.app`

Production API revision: `article-fit-api-00035-vur`

Container tag: `c25-20260802-8`

## Outcome

The minimal-input hosted workflow completed against Physical Review Letters with three supplied reference PDFs
and one manuscript PDF. It reached the confirmed milestones 0, 25, 34, 50, 56, 62, 78, 82, 84, 88, 90, 98,
and 100 without progress regression. The final analysis ID was
`45920b9f-1a97-e95b-e2f9-743aaa50e95a`.

## Findings corrected during the gate

1. APS returned HTTP 403 to automated retrieval. Resolution now reuses a previously validated journal-memory
   identity and its official Scope and Guide URLs when the publisher blocks retrieval.
2. A manuscript bibliography without a `References` heading was not delimited. The extractor now recognizes a
   dense numbered-reference tail; the supplied manuscript yielded references 1 through 67.
3. The complete evidence package exceeded the internal safe prompt limit. It is now compacted deterministically
   while preserving every manuscript anchor, bibliography record, source ID, and head/middle/tail evidence.
4. Gemini returned semantically useful JSON with blank pattern fields, non-contract priority synonyms, missing
   author-validation flags, and unsupported source IDs. The adapter now supplies only non-assertive pattern
   labels, normalizes priority synonyms, forces author validation for scientific changes, removes unsupported
   source IDs, and downgrades unsupported evidence claims to clearly labelled expert suggestions.
5. Provider or memory degradation no longer destroys an otherwise valid deterministic analysis.

## Content acceptance

- 28 recommendations were generated: 10 deterministic and 18 from `gemini-editorial-review`.
- The AI review covered all 11 required dimensions: scope fit, literature positioning, novelty/significance,
  scientific framing, theory/methodology, validation/robustness, results analysis, figures/equations, structure,
  writing, and compliance.
- Scientific interventions are marked `authorValidationRequired=true`.
- Unsupported provider source identifiers are absent from artifact citations and are disclosed through the
  proposal uncertainty field.
- The report includes an executive verdict, evidence boundary, scope fit, literature/novelty audit, scientific
  and structural upgrades, architecture, title/abstract/significance/figure plan, action plan, detailed ledger,
  sources, and a final recommendation.

## Artifact acceptance

| Artifact                | Result                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| Revised manuscript DOCX | 7,221,582 bytes; ZIP/OOXML integrity passed; original page images preserved               |
| Revised manuscript PDF  | 596,934 bytes; 38 pages; original pages interleaved with color-coded suggestion pages     |
| Revision report PDF     | 222,974 bytes; 40 pages; visual QA passed on cover, body, ledger, sources, and final page |

No raw `\\frac`, `\\begin`, `\\end`, or dollar-delimited LaTeX was found in extracted artifact text. The original
manuscript remains black and visually unchanged; proposed text is blue, and scientific-validation warnings are
red. No clipping or unreadable overflow was observed in the sampled render pages.

## Privacy and cleanup

The project endpoint returned `documents: []` immediately after successful artifact generation. Six QA projects,
including interrupted and successful runs, were then deleted through the production API; every deletion returned
HTTP 204. Local QA copies remain only in the ignored `tmp/e2e-c25/` workspace directory. The Cloud Build package
contains 188 code files (10.6 MiB) and excludes `tmp/`, `.vercel/`, and uploaded documents.

## Automated gates

- Web tests: 23 passed; statement coverage 93.34%.
- Contract tests: 6 passed; coverage 100%.
- Python tests: 133 passed; coverage 90.19%.
- Build, lint, typecheck, format check, dependency boundaries, and secret scan passed.
- Production dependency audit: 0 vulnerabilities.
- Production smoke tests passed for health and PRL resolution (`0031-9007`, official Scope and Guide URLs).
- No Cloud Run error-level events were recorded after the final promotion and hosted execution.

## Deployment and rollback

- API: `article-fit-api-00035-vur`, 100% traffic.
- Worker and retention jobs: image `worker:c25-20260802-8`.
- Frontend: Vercel deployment `dpl_Gc9WSHQzCz8j6yqppEELzH7KDWxR`.
- Immediate rollback revision: `article-fit-api-00033-tug`.
