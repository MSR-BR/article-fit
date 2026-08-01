# Change 003 validation evidence

Validated on 2026-07-31 against the fixed project runtimes.

## Automated results

- Python Docker quality target: 27 tests passed; the required 90% coverage gate passed; Ruff check/format and mypy passed.
- JavaScript Docker quality target: 10 tests passed across web and contracts; ESLint and TypeScript passed.
- Web coverage: 98.9% statements/lines, 82.5% branches, and 100% functions.
- Contract coverage: 100% statements, branches, functions, and lines.
- Container smoke test: web/API health checks and worker startup passed; temporary services and volumes were removed.
- Production npm audit: 0 vulnerabilities.

## Acceptance coverage

- Deterministic tests cover the rolling five-year window, exact ISSN matching, DOI normalization, bibliographic fingerprinting, deduplication, same-work equivalence, and exactly-three selection.
- Mocked provider contracts cover Crossref and OpenAlex parsing, Unpaywall-driven lawful locations, caching, bounded responses, `429` retry, provider failures, HTTPS/domain enforcement, DNS failures, and private-network rejection.
- Integration tests cover complete six-article research, official scope/guide snapshots, immutable version publication, optimistic concurrency failure, retrieval of an older selectable version, authentication, and incomplete-ingestion refusal.
- Anti-hallucination gates reject unknown evidence IDs, official facts without official evidence, missing locators, prompt-injection-like source instructions, and degraded profile publication.
- Shared profile serialization excludes raw private article content and private source locations. Official and open sources retain hashes, timestamps, access status, and locators.

## Limitations

- The local pilot executes research synchronously. A production deployment requires a durable asynchronous research queue with persisted stage retries and cancellation.
- PDF/HTML extraction is bounded and intentionally not fidelity-grade. A missing or weak full text produces a degraded result and no shared profile publication.
- Official pages are snapshotted and classified, while detailed rule extraction and richer language/style interpretation require an approved, schema-constrained model/evaluation set in a later refinement.
- Provider terms, rate limits, robots policies, official-domain mappings, and runtime base-image advisories require continuing operational review.
- Change 003 does not analyze or rewrite the manuscript and does not create export artifacts.
