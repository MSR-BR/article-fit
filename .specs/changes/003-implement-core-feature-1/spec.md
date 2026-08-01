# Change 003 — Journal Research and Profile

Status: `completed`

## Objective

Attempt to acquire up to three eligible journal articles plus official scope/author guidance, analyze the available reference set, and create a versioned, evidence-backed shared journal profile.

## Requirements

- Implement approved scholarly metadata/search adapters with rate limits, caching, attribution, and terms compliance.
- Find three distinct articles from the confirmed journal within the rolling five-year window and deduplicate them from uploads.
- Resolve lawful open versions of closed articles and verify same-work identity.
- Capture current official scope and author-guide evidence with timestamps, hashes, and locators.
- Extract structural/style observations from six sufficiently available full texts.
- Merge observations with the prior journal-profile version using explicit precedence, coverage, confidence, contradiction, and supersession rules.
- Publish only validated derived knowledge; private raw document text never enters the shared profile.
- Expose research status, selected sources, limitations, and a profile preview.

## Approved scope decisions

- Crossref polite REST API is the primary DOI/ISSN metadata adapter. Requests identify the application, include an operational contact, cache responses, remain sequential, and honor `429`/`Retry-After` responses.
- OpenAlex is the secondary discovery/location adapter; Unpaywall v2 verifies lawful open-access locations for DOI-bearing works. Both require an operational contact and conservative client-side throttling.
- Scope and author guidance must come from HTTPS pages on the confirmed official journal domain (or an explicitly reviewed publisher domain). Redirects to unrelated domains fail closed.
- The five-year window is calculated from the current UTC date and the article publication date, inclusively.
- Failure to obtain all three additional works is a nonblocking warning. A shared profile may use the three user-supplied full texts as its minimum article sample, provided both current official-page snapshots and all other blocking evidence requirements are satisfied.
- C3 derives journal-level observations only. It does not compare, rewrite, score, or export the user's manuscript.

## Acceptance criteria

- Every published journal fact/recommendation basis has valid provenance.
- The discovered set contains up to three eligible, distinct, date-valid journal articles; a shortfall is reported explicitly without blocking analysis.
- Alternative open versions are demonstrably the same works; no access control is bypassed.
- Profile version history is immutable, reproducible, and rollback-selectable.
- Official rules are separated from observed patterns and expert inference.
- Concurrent updates do not lose evidence or expose private content.

## Files to modify

- Journal research/profile services, provider adapters, worker stages, schemas, and migrations.
- Web research/profile evidence views and API endpoints.
- Prompt/rubric templates, validators, evaluation fixtures, tests, and provider/legal documentation.

## Tests to run

- Date filtering, journal identity, deduplication, open-version equivalence, precedence, merge, confidence, and concurrency tests.
- Mocked provider contract/error/rate-limit tests and recorded lawful integration tests.
- Prompt-injection, fabricated identifier, stale/conflicting guide, missing full text, and private-data leakage tests.
- Reproducibility and profile-version migration tests.

## Completion checklist

- [x] Approved providers and terms are documented.
- [x] Discovery and official-page acquisition meet citation rules.
- [x] Variable-size analysis accepts the three supplied articles as its minimum and reports additional-article coverage.
- [x] Shared profile publishing preserves privacy and history.
- [x] Anti-hallucination evaluations pass.
- [x] Acceptance evidence and limitations are recorded.
