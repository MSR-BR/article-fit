"""Bounded extraction of manuscript bibliography and literature-search evidence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
ARXIV_PATTERN = re.compile(r"\b(?:arXiv\s*:\s*)?(\d{4}\.\d{4,5})(?:v\d+)?\b", re.I)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
REFERENCE_HEADING = re.compile(r"(?im)^\s*(?:references|bibliography|literature cited)\s*$")
NUMBERED_REFERENCE = re.compile(r"(?m)^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+")


@dataclass(frozen=True)
class BibliographyEntry:
    number: int
    raw: str
    doi: str | None
    arxiv_id: str | None
    year: int | None

    @property
    def source_id(self) -> str:
        digest = hashlib.sha256(self.raw.encode()).hexdigest()[:24]
        return f"manuscript-reference-{digest}"


@dataclass(frozen=True)
class ManuscriptLiteratureContext:
    title: str
    abstract: str
    topic: str
    bibliography: tuple[BibliographyEntry, ...]
    limitations: tuple[str, ...]


def _section(text: str, heading: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"(?m)^\s*(?:\d+(?:\.\d+)*\s+)?[A-Z][A-Za-z -]{2,40}\s*$", rest)
    return rest[: next_heading.start() if next_heading else len(rest)].strip()


def extract_bibliography(text: str, *, maximum: int = 80) -> tuple[BibliographyEntry, ...]:
    heading = REFERENCE_HEADING.search(text)
    if not heading:
        return ()
    body = text[heading.end() :].strip()
    matches = list(NUMBERED_REFERENCE.finditer(body))
    chunks: list[tuple[int, str]] = []
    if matches:
        for index, match in enumerate(matches[:maximum]):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            number = int(match.group(1) or match.group(2) or index + 1)
            chunks.append((number, body[match.end() : end]))
    else:
        lines = [line.strip() for line in body.splitlines() if len(line.strip()) >= 20]
        chunks = [(index, line) for index, line in enumerate(lines[:maximum], 1)]
    entries: list[BibliographyEntry] = []
    for number, chunk in chunks:
        raw = " ".join(chunk.split())[:2_000]
        if len(raw) < 12:
            continue
        doi_match = DOI_PATTERN.search(raw)
        arxiv_match = ARXIV_PATTERN.search(raw)
        years = YEAR_PATTERN.findall(raw)
        entries.append(
            BibliographyEntry(
                number=number,
                raw=raw,
                doi=(doi_match.group(0).rstrip(".,;)").casefold() if doi_match else None),
                arxiv_id=(arxiv_match.group(1) if arxiv_match else None),
                year=(int(years[-1]) if years else None),
            )
        )
    return tuple(entries)


def extract_manuscript_literature_context(text: str) -> ManuscriptLiteratureContext:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = next(
        (
            line
            for line in lines[:20]
            if len(line) >= 12 and not re.fullmatch(r"(?:abstract|introduction|manuscript|preprint)", line, re.I)
        ),
        "Submitted manuscript",
    )[:300]
    abstract = _section(text, "abstract")
    if not abstract:
        abstract = " ".join(lines[1:20])
    abstract = " ".join(abstract.split())[:4_000]
    topic_seed = f"{title}. {abstract}"
    topic = " ".join(topic_seed.split())[:180].rstrip(" ,;:")
    bibliography = extract_bibliography(text)
    limitations: list[str] = []
    if not bibliography:
        limitations.append("No reliably delimited bibliography was extracted from the manuscript.")
    elif len(bibliography) < 5:
        limitations.append("Only a small number of bibliography entries could be extracted reliably.")
    return ManuscriptLiteratureContext(title, abstract, topic, bibliography, tuple(limitations))


def manuscript_reference_evidence(context: ManuscriptLiteratureContext) -> list[dict[str, object]]:
    return [
        {
            "sourceId": entry.source_id,
            "sourceType": "manuscript-reference",
            "label": f"[{entry.number}] {entry.raw}",
            "identifier": entry.doi or (f"arXiv:{entry.arxiv_id}" if entry.arxiv_id else ""),
            "year": entry.year or "",
            "status": "manuscript-supplied-unverified",
        }
        for entry in context.bibliography
    ]


def _candidate_label(item: dict[str, object]) -> str:
    for key in ("title", "citation", "displayName", "name", "paperTitle"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())[:1_000]
    return "Literature candidate"


def recent_literature_evidence(
    references: list[dict[str, object]], top_papers: list[dict[str, object]]
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in [*top_papers, *references][:60]:
        label = _candidate_label(item)
        identifier = next(
            (
                str(item[key])
                for key in ("doi", "arxivId", "url", "id")
                if isinstance(item.get(key), str | int) and str(item[key]).strip()
            ),
            "",
        )
        identity = json.dumps([label.casefold(), identifier.casefold()], ensure_ascii=False)
        digest = hashlib.sha256(identity.encode()).hexdigest()[:24]
        if digest in seen:
            continue
        seen.add(digest)
        year_value = next((item.get(key) for key in ("year", "publishedYear", "publicationYear") if item.get(key)), "")
        evidence.append(
            {
                "sourceId": f"recent-literature-{digest}",
                "sourceType": "research-starter-candidate",
                "label": label,
                "identifier": identifier[:300],
                "year": str(year_value)[:20],
                "status": "recent-literature-candidate",
            }
        )
    return evidence


def source_catalog(evidence: list[dict[str, object]]) -> dict[str, str]:
    return {
        str(item["sourceId"]): " — ".join(
            value for value in (str(item.get("label", "")), str(item.get("identifier", ""))) if value
        )[:1_300]
        for item in evidence
        if item.get("sourceId")
    }
