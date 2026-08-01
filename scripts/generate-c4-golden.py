"""Generate synthetic C4 artifacts for render and parity QA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from journal_matcher_api.manuscript_analysis import annotate_docx, create_docx, create_pdf, validate_artifacts


def main() -> int:
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    manuscript = """Synthetic Manuscript for Artifact Validation
Abstract
This synthetic abstract reports no real study and contains no private or identifying information.
Introduction
This fixture exists only to validate document architecture, color labels, typography, and rendering.
Methods
We generated deterministic text without participants, measurements, or scientific claims.
Results
The artifact generator produced a structurally valid synthetic review bundle.
Discussion
The fixture must not be interpreted as scholarly evidence.
Conclusion
Visual inspection confirms whether headings, paragraphs, and revision annotations remain legible.
References
No references are required for this synthetic validation fixture."""
    recommendation = {
        "id": "synthetic-recommendation",
        "category": "structure",
        "anchor": "paragraph:2",
        "decision": "modified",
        "modifiedText": "Author-verified synthetic revision note.",
        "rationale": "Synthetic rendering check.",
    }
    original_docx = create_docx(manuscript, [], reconstructed=False)
    docx = annotate_docx(original_docx, [recommendation])
    revised_pdf = create_pdf(
        "Revised manuscript - synthetic review copy",
        [
            *manuscript.splitlines(),
            "",
            "Accepted revision notes:",
            "[structure] Author-verified synthetic revision note.",
        ],
    )
    report_pdf = create_pdf(
        "Journal Matcher synthetic revision report",
        [
            "1. Executive summary",
            "No journal acceptance is guaranteed.",
            "2. Inputs and source coverage",
            "This report contains only synthetic validation content.",
            "3. Guide compliance matrix",
            "No real guide rules are used by this fixture.",
            "4. Scientific and methodological review",
            "No scientific claims are evaluated by this fixture.",
            "5. Article architecture and journal fit",
            "Synthetic architecture check only.",
            "6. Presentation, language, and layout",
            "Color-independent category labels are required.",
            "7. Change ledger",
            "STRUCTURE | modified | paragraph:2 | Author-verified synthetic revision note.",
            "8. Unresolved items and author actions",
            "None in this synthetic fixture.",
            "9. Sources and reproducibility",
            "Fixture: synthetic-c4-golden; model: none.",
        ],
    )
    manifest = json.dumps(
        {
            "schemaVersion": "1.0",
            "fixture": "synthetic-c4-golden",
            "model": None,
            "containsPrivateData": False,
        },
        indent=2,
    ).encode()
    validate_artifacts(docx, revised_pdf, report_pdf, manifest)
    artifacts = {
        "revised-manuscript.docx": docx,
        "revised-manuscript.pdf": revised_pdf,
        "revision-report.pdf": report_pdf,
        "provenance-manifest.json": manifest,
    }
    for name, content in artifacts.items():
        (output / name).write_bytes(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
