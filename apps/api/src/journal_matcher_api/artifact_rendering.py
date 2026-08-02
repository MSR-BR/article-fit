"""Professional, evidence-led PDF artifacts without external rendering services."""

from __future__ import annotations

import re
import textwrap
from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO

from pypdf import PdfReader, PdfWriter

NAVY = (0.08, 0.20, 0.36)
TEAL = (0.02, 0.43, 0.48)
BLUE = (0.12, 0.31, 0.55)
RED = (0.68, 0.12, 0.12)
GREEN = (0.16, 0.42, 0.28)
ORANGE = (0.72, 0.31, 0.08)
GRAY = (0.35, 0.38, 0.39)
LIGHT = (0.95, 0.96, 0.96)
PALE_BLUE = (0.93, 0.96, 0.99)
BLACK = (0.0, 0.0, 0.0)

CATEGORY_LABELS = {
    "form": "Form and layout",
    "structure": "Article architecture",
    "language": "Language and rhetoric",
    "content": "Content development",
    "scientific-question": "Scientific-depth question",
    "compliance": "Journal compliance",
    "journal-format": "Journal compliance",
    "methodology-reporting": "Methods presentation",
    "scientific-concern": "Scientific-depth question",
    "unresolved": "Author decision",
}


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _latin(value: object) -> str:
    text = str(value or "")
    text = text.replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    return text.encode("latin-1", errors="replace").decode("latin-1")


class EditorialPdf:
    """Small paginated PDF compositor with predictable typography and hierarchy."""

    def __init__(self, *, running_left: str, running_right: str) -> None:
        self.running_left = _latin(running_left)[:52]
        self.running_right = _latin(running_right)[:42]
        self.pages: list[list[str]] = []
        self.y = 0.0
        self.page_number = 0
        self._title_page = False

    @property
    def commands(self) -> list[str]:
        return self.pages[-1]

    def new_page(self, *, title_page: bool = False) -> None:
        self.pages.append([])
        self.page_number += 1
        self._title_page = title_page
        if title_page:
            self.y = 690
            return
        self.commands.extend(
            [
                "0.08 0.20 0.36 RG 72 749 m 540 749 l S",
                self._text_command(72, 760, self.running_left, "F3", 8.5, NAVY),
                self._text_command(540, 760, self.running_right, "F3", 8.5, NAVY, align="right"),
                self._text_command(306, 28, str(self.page_number - 1), "F3", 8.5, GRAY, align="center"),
            ]
        )
        self.y = 720

    def _text_command(
        self,
        x: float,
        y: float,
        value: str,
        font: str,
        size: float,
        color: tuple[float, float, float],
        *,
        align: str = "left",
    ) -> str:
        text = _latin(value)
        estimated = len(text) * size * 0.48
        if align == "right":
            x -= estimated
        elif align == "center":
            x -= estimated / 2
        r, g, b = color
        return (
            f"BT /{font} {size:.1f} Tf {r:.3f} {g:.3f} {b:.3f} rg "
            f"1 0 0 1 {x:.1f} {y:.1f} Tm ({_pdf_escape(text)}) Tj ET"
        )

    def _ensure(self, height: float) -> None:
        if self.y - height < 54:
            self.new_page()

    def text_at(
        self,
        x: float,
        y: float,
        value: str,
        *,
        font: str = "F1",
        size: float = 10,
        color: tuple[float, float, float] = BLACK,
        align: str = "left",
    ) -> None:
        self.commands.append(self._text_command(x, y, value, font, size, color, align=align))

    def rule(self, y: float, *, color: tuple[float, float, float] = NAVY, width: float = 1) -> None:
        r, g, b = color
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG {width:.1f} w 72 {y:.1f} m 540 {y:.1f} l S")

    def heading(self, value: str, *, level: int = 1) -> None:
        size = 18 if level == 1 else 13
        color = NAVY if level == 1 else TEAL
        before = 18 if level == 1 else 12
        after = 10 if level == 1 else 7
        self._ensure(before + size + after)
        self.y -= before
        self.text_at(72, self.y, value, font="F4", size=size, color=color)
        self.y -= size + after

    def paragraph(
        self,
        value: object,
        *,
        color: tuple[float, float, float] = BLACK,
        font: str = "F1",
        size: float = 10.2,
        indent: float = 0,
        gap: float = 8,
    ) -> None:
        text = " ".join(_latin(value).split())
        if not text:
            self.y -= gap
            return
        width = max(36, int((468 - indent) / (size * 0.52)))
        lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]
        line_height = size * 1.34
        self._ensure(len(lines) * line_height + gap)
        for line in lines:
            self.text_at(72 + indent, self.y, line, font=font, size=size, color=color)
            self.y -= line_height
        self.y -= gap

    def bullet(self, value: object, *, color: tuple[float, float, float] = BLACK) -> None:
        self._ensure(28)
        self.text_at(79, self.y, "-", font="F4", size=10.2, color=TEAL)
        self.paragraph(value, color=color, indent=20, gap=4)

    def label_value(self, label: str, value: object, *, value_color: tuple[float, float, float] = BLACK) -> None:
        self._ensure(30)
        self.text_at(72, self.y, label.upper(), font="F4", size=8.2, color=GRAY)
        self.y -= 13
        self.paragraph(value, color=value_color, size=9.8, gap=7)

    def callout(self, title: str, body: object, *, color: tuple[float, float, float] = BLUE) -> None:
        body_text = " ".join(_latin(body).split())
        lines = textwrap.wrap(body_text, width=78, break_long_words=False, break_on_hyphens=False) or [""]
        height = 39 + len(lines) * 13
        self._ensure(height + 10)
        bottom = self.y - height + 8
        r, g, b = PALE_BLUE
        self.commands.append(f"q {r:.3f} {g:.3f} {b:.3f} rg 72 {bottom:.1f} 468 {height:.1f} re f Q")
        r, g, b = color
        self.commands.append(f"q {r:.3f} {g:.3f} {b:.3f} rg 72 {bottom:.1f} 5 {height:.1f} re f Q")
        self.text_at(88, self.y - 13, title, font="F4", size=10.5, color=color)
        cursor = self.y - 31
        for line in lines:
            self.text_at(88, cursor, line, font="F1", size=9.5, color=BLACK)
            cursor -= 13
        self.y = bottom - 10

    def recommendation(self, number: int, item: dict[str, object]) -> None:
        category = CATEGORY_LABELS.get(str(item.get("category")), str(item.get("category", "Editorial review")))
        severity = str(item.get("severity", "recommended")).replace("-", " ").title()
        self.heading(f"{number}. {category}", level=2)
        self.paragraph(
            f"{severity} | {str(item.get('basis', 'expert-suggestion')).replace('-', ' ')} | "
            f"{item.get('anchor', 'document')}",
            color=GRAY,
            font="F3",
            size=8.8,
            gap=7,
        )
        original = str(item.get("originalText") or "").strip()
        if original:
            self.label_value("Current manuscript", original[:1400])
        self.label_value("What needs improvement", item.get("rationale", ""))
        proposed = item.get("modifiedText") or item.get("proposedText")
        if proposed:
            self.label_value("Suggested revision", proposed, value_color=BLUE)
        else:
            self.label_value(
                "Author action",
                "Revise this passage following the recommendation above; retain the scientific claim only after "
                "author verification.",
                value_color=BLUE,
            )
        if item.get("scientificImpact") or item.get("authorValidationRequired"):
            self.paragraph(
                "Author validation required: this suggestion may affect scientific meaning and is not presented "
                "as a verified result.",
                color=RED,
                font="F4",
                size=8.8,
                gap=10,
            )
        self.rule(self.y, color=(0.82, 0.84, 0.85), width=0.6)
        self.y -= 8

    def build(self) -> bytes:
        objects: list[bytes] = [b"", b""]
        fonts = [
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Italic >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]
        objects.extend(fonts)
        page_ids: list[int] = []
        for commands in self.pages:
            stream = "\n".join(commands).encode("latin-1", errors="replace")
            content_id = len(objects) + 1
            objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
            page_id = len(objects) + 1
            page_ids.append(page_id)
            objects.append(
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font "
                    "<< /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode()
            )
        objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
        output = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, 1):
            offsets.append(len(output))
            output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode())
        output.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
        return bytes(output)


def _rank(item: dict[str, object]) -> tuple[int, str]:
    order = {"required": 0, "strongly-recommended": 1, "question": 2, "recommended": 3, "optional": 4}
    return order.get(str(item.get("severity")), 5), str(item.get("anchor", ""))


def create_editorial_report_pdf(
    *,
    journal_title: str,
    manuscript_title: str,
    recommendations: list[dict[str, object]],
    rules: list[dict[str, object]],
    limitations: list[str],
    reference_count: int,
) -> bytes:
    items = sorted((item for item in recommendations if item.get("decision") != "rejected"), key=_rank)
    required = sum(item.get("severity") == "required" for item in items)
    high = sum(item.get("severity") == "strongly-recommended" for item in items)
    scientific = sum(bool(item.get("scientificImpact") or item.get("authorValidationRequired")) for item in items)
    verdict = "MAJOR REVISION BEFORE SUBMISSION" if required or high else "TARGETED REVISION ADVISED"

    pdf = EditorialPdf(running_left=manuscript_title or "Submitted manuscript", running_right="Article Fit assessment")
    pdf.new_page(title_page=True)
    pdf.text_at(306, 650, "ARTICLE FIT", font="F4", size=11, color=TEAL, align="center")
    title_lines = textwrap.wrap(f"{journal_title} submission assessment", width=34, break_long_words=False)
    title_y = 610
    for line in title_lines:
        pdf.text_at(306, title_y, line, font="F4", size=25, color=NAVY, align="center")
        title_y -= 31
    manuscript_lines = textwrap.wrap(manuscript_title or "Submitted manuscript", width=68, break_long_words=False)
    manuscript_y = title_y - 12
    for line in manuscript_lines[:2]:
        pdf.text_at(306, manuscript_y, line, font="F2", size=14, color=GRAY, align="center")
        manuscript_y -= 20
    pdf.rule(520, color=NAVY, width=1.1)
    pdf.text_at(90, 485, "A supervisor-level editorial comparison with the journal's", font="F1", size=11, color=BLACK)
    pdf.text_at(90, 467, "official requirements and observed publication pattern", font="F1", size=11, color=BLACK)
    pdf.text_at(
        90,
        420,
        "This report evaluates writing, structure, presentation, methodological",
        font="F1",
        size=10.5,
        color=BLACK,
    )
    pdf.text_at(
        90,
        403,
        "communication, and scientific depth. It does not compare the manuscript's",
        font="F1",
        size=10.5,
        color=BLACK,
    )
    pdf.text_at(
        90,
        386,
        "physics content with the reference articles and does not predict acceptance.",
        font="F1",
        size=10.5,
        color=BLACK,
    )
    pdf.text_at(
        306,
        100,
        "Editorial preparation document - author verification required",
        font="F3",
        size=9,
        color=GRAY,
        align="center",
    )

    pdf.new_page()
    pdf.heading("1  Executive verdict")
    pdf.callout(
        verdict,
        f"{required} mandatory compliance issue(s), {high} high-priority editorial issue(s), and "
        f"{scientific} suggestion(s) requiring scientific author validation were identified.",
        color=ORANGE if required or high else GREEN,
    )
    pdf.paragraph(
        "The manuscript should not be judged against the subject matter of the reference papers. The relevant "
        "comparison is how published articles in the target journal frame their contribution, organize the "
        "argument, present methods and results, control length, and communicate significance to the journal's "
        "readership."
    )
    pdf.heading("Readiness dashboard", level=2)
    pdf.bullet(f"Official compliance: {required} unresolved mandatory item(s).")
    pdf.bullet(f"Architecture and journal pattern: {high} high-priority deviation(s).")
    pdf.bullet(f"Scientific-depth safeguards: {scientific} item(s) must be checked by the authors or a domain expert.")
    pdf.bullet(
        f"Evidence base: official Scope and Guide for Authors plus {reference_count} supplied/found journal article(s)."
    )

    pdf.heading("2  Evidence boundary")
    pdf.paragraph(
        "Official requirements are treated as requirements only when supported by validated official guidance. "
        "Patterns observed in published articles are advisory, not rules. Editorial suggestions are explicitly "
        "identified as expert or AI-assisted recommendations."
    )
    for limitation in limitations:
        pdf.bullet(limitation, color=GRAY)

    pdf.heading("3  Priority action plan")
    for index, item in enumerate(items[:10], 1):
        category = CATEGORY_LABELS.get(str(item.get("category")), str(item.get("category", "Editorial")))
        action = item.get("proposedText") or item.get("rationale") or "Review this item."
        pdf.bullet(f"{index}. {category} at {item.get('anchor', 'document')}: {action}")
    if len(items) > 10:
        pdf.paragraph(f"The detailed ledger contains {len(items) - 10} additional recommendations.", color=GRAY)

    pdf.heading("4  Official-guide compliance")
    if not rules:
        pdf.paragraph(
            "No machine-verifiable official rule was extracted. Consult the supplied official guidance directly "
            "before submission.",
            color=RED,
        )
    for rule in rules:
        status = str(rule.get("status", "unresolved")).upper()
        key = str(rule.get("key", "official requirement")).replace("-", " ").title()
        pdf.bullet(f"{key}: {status}. The detailed recommendation states the required author action.")

    pdf.heading("5  Journal-pattern comparison")
    categories: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in items:
        categories[
            CATEGORY_LABELS.get(str(item.get("category")), str(item.get("category", "Editorial review")))
        ].append(item)
    for category, category_items in categories.items():
        pdf.heading(category, level=2)
        pdf.paragraph(
            f"{len(category_items)} issue(s) were identified in this dimension. The comparison concerns editorial "
            "execution and presentation, not similarity of scientific subject matter."
        )
        for item in category_items[:4]:
            pdf.bullet(f"{item.get('anchor', 'document')}: {item.get('rationale', '')}")

    pdf.heading("6  Detailed revision ledger")
    pdf.paragraph(
        "Each entry states the location, the observed gap, the action to take, and proposed wording when a "
        "responsible rewrite can be made without inventing scientific content. Blue wording is a suggestion, "
        "not an automatic replacement."
    )
    for index, item in enumerate(items, 1):
        pdf.recommendation(index, item)

    pdf.heading("7  Submission gate")
    pdf.callout(
        "Recommended next pass",
        "Resolve all mandatory items; complete the high-priority architecture and presentation revisions; have "
        "the authors validate every scientific-meaning suggestion; then rerun Article Fit with the revised "
        "manuscript to measure remaining journal-pattern gaps.",
        color=TEAL,
    )
    pdf.paragraph(
        "No responsible editorial analysis can guarantee acceptance. The purpose of this report is to make the "
        "manuscript more legible, compliant, and recognizable as a submission written for the target journal."
    )
    return pdf.build()


def create_review_notes_pdf(*, title: str, anchor: str, recommendations: list[dict[str, object]]) -> bytes:
    pdf = EditorialPdf(running_left=title, running_right="Color-coded revision suggestions")
    pdf.new_page()
    pdf.heading(f"Suggestions for {anchor}")
    pdf.paragraph(
        "The preceding source page is retained unchanged. Original manuscript content remains black on the source "
        "page; the blue text below contains proposed revisions or author actions."
    )
    for index, item in enumerate(recommendations, 1):
        pdf.recommendation(index, item)
    return pdf.build()


def create_pdf_review_copy(
    *, original_pdf: bytes, manuscript_title: str, recommendations: list[dict[str, object]]
) -> bytes:
    """Keep every source PDF page intact and interleave anchored suggestion pages."""
    source = PdfReader(BytesIO(original_pdf), strict=False)
    by_page: dict[int, list[dict[str, object]]] = defaultdict(list)
    unanchored: list[dict[str, object]] = []
    for item in sorted((entry for entry in recommendations if entry.get("decision") != "rejected"), key=_rank):
        match = re.fullmatch(r"page:(\d+)", str(item.get("anchor", "")))
        if match and 1 <= int(match.group(1)) <= len(source.pages):
            by_page[int(match.group(1))].append(item)
        else:
            unanchored.append(item)
    writer = PdfWriter()
    for page_number, page in enumerate(source.pages, 1):
        writer.add_page(page)
        if by_page[page_number]:
            notes = PdfReader(
                BytesIO(
                    create_review_notes_pdf(
                        title=manuscript_title,
                        anchor=f"source page {page_number}",
                        recommendations=by_page[page_number],
                    )
                )
            )
            for note_page in notes.pages:
                writer.add_page(note_page)
    if unanchored:
        notes = PdfReader(
            BytesIO(
                create_review_notes_pdf(
                    title=manuscript_title, anchor="the manuscript as a whole", recommendations=unanchored
                )
            )
        )
        for note_page in notes.pages:
            writer.add_page(note_page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def create_text_review_pdf(
    *, manuscript_title: str, manuscript_text: str, recommendations: list[dict[str, object]]
) -> bytes:
    pdf = EditorialPdf(running_left=manuscript_title, running_right="Revised manuscript review copy")
    pdf.new_page()
    pdf.heading("Original manuscript")
    pdf.paragraph(
        "Original text is shown in black. Color-coded suggestions follow the manuscript. For exact editable "
        "template preservation, submit the manuscript as DOCX."
    )
    for paragraph in (part.strip() for part in manuscript_text.splitlines() if part.strip()):
        pdf.paragraph(paragraph, size=9.2, gap=5)
    pdf.heading("Color-coded suggestions")
    for index, item in enumerate(sorted(recommendations, key=_rank), 1):
        if item.get("decision") != "rejected":
            pdf.recommendation(index, item)
    return pdf.build()


def pdf_text(value: bytes) -> str:
    reader = PdfReader(BytesIO(value), strict=False)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def recommendation_texts(recommendations: Iterable[dict[str, object]]) -> list[str]:
    return [
        str(item.get("modifiedText") or item.get("proposedText") or item.get("rationale") or "")
        for item in recommendations
        if item.get("decision") != "rejected"
    ]
