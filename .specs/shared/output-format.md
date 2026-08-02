# Output Format

## Deliverable bundle

Each completed job produces:

1. `revised-manuscript.docx` — editable proposed revision with visible color-coded changes and comments/annotations.
2. `revised-manuscript.pdf` — stable review rendering of the same proposed revision.
3. `revision-report.pdf` — complete recommendation ledger and compliance report.

Source provenance, model identifiers, content hashes, and validation metadata remain internal. They are not exposed as an end-user download.

For a PDF input, the revised PDF retains every original page unchanged and interleaves color-coded suggestion pages. If faithful editable reconstruction is not possible, the system must warn the user and label the DOCX as reconstructed. For a DOCX input, the original package and visual system control the revised Word document.

## Change categories and colors

Colors are supplemented by labels/icons so meaning is not color-dependent:

- Blue — language and clarity.
- Purple — structure and argument flow.
- Orange — journal formatting or layout requirement.
- Green — methodological/reporting improvement.
- Red — scientific-content concern requiring author verification.
- Gray — unresolved question or missing evidence.

Deletion and insertion must remain distinguishable in monochrome. The final palette must pass contrast and print tests.

## Recommendation record

Every change has:

- stable change ID;
- manuscript locator and original text;
- proposed text or explicit author action;
- category and severity (`required`, `strongly recommended`, `optional`, `question`);
- rationale;
- basis (`official requirement`, `observed pattern`, `expert suggestion`);
- source links/locators and evidence coverage;
- confidence and uncertainty;
- scientific-meaning impact flag;
- user decision (`pending`, `accepted`, `rejected`, `modified`).

## Revision report sections

1. Executive summary and prominent “no acceptance guarantee” notice.
2. Input completeness, journal identity, analyzed article set, and source limitations.
3. Official scope fit and author-guide compliance matrix.
4. High-priority scientific and methodological issues.
5. Article architecture and section-by-section analysis.
6. Language, presentation, figures/tables, references, declarations, and layout.
7. Full change ledger ordered by severity and manuscript location.
8. Unresolved questions and required author actions.
9. Sources, retrieval dates, journal-profile version, confidence, and reproducibility summary.

## Integrity requirements

- DOCX and PDF convey the same visible proposal set, including pending suggestions and excluding rejected items.
- Headings, tables, figures, equations, citations, cross-references, footnotes, and supplementary references are preserved or explicitly flagged.
- Page/paragraph locators in the report resolve to the output and, where possible, the original.
- No internal prompts, credentials, private storage URLs, or other users’ content appear in artifacts.
