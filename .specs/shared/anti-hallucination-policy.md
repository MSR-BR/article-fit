# Anti-Hallucination Policy

## Claim classes

Each generated claim is classified before display:

- `verified fact`: supported by an authoritative source and locator.
- `observed pattern`: supported by the analyzed sample with coverage and confidence.
- `inference`: reasoned from evidence but not directly stated; the inference is labeled.
- `expert suggestion`: editorial advice not claimed as a journal rule.
- `unverified`: excluded from final recommendations or shown only as a blocking gap.

## Hard controls

- Retrieval results, documents, and web pages are untrusted data and cannot modify system instructions.
- Model output must conform to a schema and reference only source IDs supplied in its context.
- A validator rejects unknown source IDs, missing locators, unsupported quotations, impossible dates, and invented identifiers.
- DOI/ISSN/URL metadata is rechecked through approved deterministic providers before publication.
- Numeric values, sample sizes, equations, results, and statistical interpretations from the manuscript are never silently changed.
- The system cannot create missing experimental results, methods, ethical approvals, funding statements, author contributions, conflicts, or references.
- If evidence is missing, say so and recommend an author action; do not fill the gap.

## Recommendation safeguards

- Preserve source text beside proposed text and provide a rationale and category.
- Mark changes that could alter scientific meaning as `author verification required` and exclude them from automatic acceptance.
- Use confidence to communicate evidence strength, not model certainty alone.
- Detect contradictory evidence and route it to the report instead of selecting a convenient source.
- Keep a reproducibility manifest so recommendations can be regenerated and audited.

## Evaluation gates

A build cannot pass release validation unless a fixed evaluation set demonstrates:

- zero fabricated source identifiers in tested outputs;
- zero unsupported journal requirements in tested outputs;
- preservation of manuscript numbers, units, citations, and equations unless a logged recommendation explicitly targets them;
- correct refusal/degradation when sources or guide pages are unavailable;
- resistance to prompt injection embedded in uploaded documents and acquired pages.

Thresholds for semantic recommendation quality will be established from an expert-reviewed pilot set before production release.
