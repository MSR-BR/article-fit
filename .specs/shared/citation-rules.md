# Citation and Evidence Rules

## Required provenance

Every externally verifiable journal fact and every recommendation based on a source must record:

- canonical source URL and source type;
- title, publisher/repository, DOI/identifier when available;
- publication/effective date and retrieval timestamp;
- content hash or snapshot identifier where legally permitted;
- exact page, section, paragraph, or bounded excerpt locator;
- access/license status;
- which claim or recommendation the evidence supports.

## Discovery rules

- Confirm journal identity using canonical title and ISSN; do not rely on name alone.
- Enforce the rolling five-year publication window deterministically.
- Deduplicate the three discovered articles against user uploads and each other using DOI, repository identifiers, and bibliographic fingerprints.
- Prefer final open-access versions. If closed, seek lawful repository copies of the same work, including arXiv title searches, and verify equivalence using DOI/title/authors/year/version metadata.
- Do not substitute a merely similar article when the claim is that it is the same article.
- Record unsuccessful searches and access limitations.

## Output rules

- Official requirements are cited to official pages.
- Observed writing tendencies cite the supporting article set and report sample coverage (for example, 4 of 6), never false universality.
- Recommendations derived from general editorial judgment are labeled `expert suggestion` and are not attributed to the journal.
- The revised manuscript must not gain a scholarly citation unless the author explicitly approves it and the cited work has been verified.
- Quotes are minimal and license/copyright compliant; use paraphrase plus precise locator by default.
- Links must be resolvable at validation time or marked unavailable with the last successful retrieval date.

## Conflict handling

- Official current guidance overrides observed formatting patterns.
- Newer official guidance overrides an older official snapshot, while preserving history.
- If two current official sources conflict, report both, mark the rule unresolved, and avoid automatic reformatting for that rule.
- Retractions, corrections, expressions of concern, and version differences must be surfaced when detected by approved metadata sources.
