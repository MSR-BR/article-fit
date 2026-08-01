# Assumptions and Open Decisions

## Explicit assumptions

1. The first release is a human-in-the-loop decision-support tool, not an autonomous publication or submission system.
2. The user identifies the target journal and supplies one manuscript plus three reference articles. Journal identity is confirmed before research begins.
3. The system may retrieve only metadata, abstracts, and full text that it is legally permitted to access. It must not bypass paywalls or access controls.
4. “Last five years” means a rolling five-year window based on publication date at the time a job starts.
5. A discovered open version must be matched to the publisher version using identifiers and bibliographic evidence; title similarity alone is insufficient.
6. The shared journal profile contains derived style and structural observations, factual journal requirements, provenance, timestamps, and confidence—not copyrighted full text.
7. Uploaded manuscripts and reference files remain private to the submitting workspace and are never used to enrich the cross-user journal profile as raw content.
8. The product suggests revisions and can produce a revised copy, but material scientific claims, interpretations, and citations require author approval.
9. The MVP supports English-language manuscripts and journals. Internationalization is future work.
10. The initial interface is a responsive web application with asynchronous processing.

## Decisions required before Change 001

- Hosting region and data-residency requirements.
- Authentication model for the pilot (invitation-only is recommended).
- Retention period for uploads, generated files, and job logs.
- Approved AI model/provider and whether zero-retention processing is contractually available.
- Approved scholarly discovery providers and their credentials/terms.
- Whether DOCX tracked changes are mandatory in the MVP. The proposed baseline uses visible colored edits plus a change ledger because robust native Word tracked changes require additional document-processing validation.
- Maximum manuscript/reference file size and target processing-time service level.
- Whether the target-journal input must be DOI/ISSN, journal URL, or a user-entered name followed by confirmation.

## Out of scope for the MVP

- Automatic journal submission, acceptance prediction, fabricated reviewer simulation, plagiarism adjudication, citation-count optimization, collaborative editing, billing, and mobile-native apps.
- Training or fine-tuning a model on publisher articles.
- Scraping that violates robots rules, licenses, or publisher terms.
- Guaranteeing acceptance or replacing scientific, statistical, ethical, or legal review.
