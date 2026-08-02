# Project Rules

## Product rules

1. Never promise journal acceptance or present a recommendation as editorial certainty.
2. Preserve the original manuscript only in memory/private temporary storage while generating a separate edited output; do not retain the original after terminal processing.
3. A user can inspect, accept, reject, or modify every proposed change.
4. Scientific-content changes are visibly distinguished from language, structure, layout, and compliance changes.
5. Never invent data, analyses, citations, quotations, DOIs, journal rules, or article access locations.
6. Never bypass paywalls, authentication, robots restrictions, licenses, or provider terms.
7. Official author instructions take priority over inferred article patterns. Conflicts are reported, not silently resolved.
8. The system must disclose source coverage, retrieval dates, profile version, and confidence.
9. Cross-run learning is journal-scoped and limited to versioned, derived conclusions backed by permissible sources. Private raw content, filenames, hashes, and source identifiers are neither shared nor retained.
10. Uploaded originals and extracted private text are hard-deleted on terminal processing; private outputs and orphaned uploads are hard-deleted within 24 hours.
11. The MVP has no end-user login. The public browser reaches data services only through a server-side proxy protected by an internal credential.

## Specification-driven workflow

- Implement changes in numerical order unless a dependency revision is approved and documented.
- Before implementation, set the change status to `approved` and record scope decisions.
- If implementation reveals a new requirement, update the change specification before writing that behavior.
- A change is complete only when acceptance criteria, tests, documentation, migrations, security review, and checklist are complete.
- Future features remain in the backlog and must not leak into MVP code paths.

## Source hierarchy

For journal requirements, use this order:

1. Current official journal “Guide for Authors” or equivalent.
2. Current official publisher/journal scope and policy pages.
3. Official reporting or ethics standards explicitly incorporated by the journal.
4. Bibliographic metadata from authoritative registries.
5. Lawfully accessible article full text.
6. Abstract/metadata only, clearly labeled as insufficient for writing-pattern analysis.

## Stop conditions

The job must stop or degrade explicitly when:

- journal identity cannot be confirmed;
- fewer than three user-supplied reference articles have sufficient extractable content;
- the official guide cannot be found or its currency cannot be established;
- input extraction quality is too poor for reliable anchors;
- sources materially conflict and no authoritative resolution exists;
- output validation detects missing content, broken citations, or layout corruption.

Degraded runs may produce a diagnostic report, but must not imply a complete journal match.
