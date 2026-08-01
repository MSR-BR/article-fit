"""Evidence-backed journal identity resolution for the user-supplied candidate."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class JournalResolutionError(ValueError):
    """The supplied evidence cannot establish a unique journal identity."""


@dataclass(frozen=True)
class ResolvedJournal:
    title: str
    issn: str
    official_domain: str
    homepage_url: str
    source_id: str
    confidence: float


@dataclass(frozen=True)
class OfficialGuidance:
    scope_url: str
    guide_url: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None
            self._text = []


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _candidate_score(query: str, title: str, alternate_titles: list[str]) -> float:
    needle = _normalized(query)
    names = [_normalized(title), *(_normalized(item) for item in alternate_titles)]
    if needle in names:
        return 1.0
    return max((SequenceMatcher(None, needle, name).ratio() for name in names), default=0.0)


def resolve_openalex_sources(query: str, payload: dict[str, object]) -> ResolvedJournal:
    """Resolve one journal from a bounded OpenAlex Sources response."""
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise JournalResolutionError("Journal metadata provider returned an invalid response")
    candidates: list[tuple[float, ResolvedJournal]] = []
    for raw in raw_results[:10]:
        if not isinstance(raw, dict) or raw.get("type") != "journal":
            continue
        title = raw.get("display_name")
        homepage = raw.get("homepage_url")
        issn = raw.get("issn_l")
        source_id = raw.get("id")
        alternates = raw.get("alternate_titles", [])
        if not all(isinstance(item, str) and item for item in (title, homepage, issn, source_id)):
            continue
        parsed = urlparse(str(homepage))
        domain = (parsed.hostname or "").casefold()
        if parsed.scheme not in {"http", "https"} or not domain or domain in {"doi.org", "openalex.org"}:
            continue
        secure_homepage = parsed._replace(scheme="https").geturl()
        alternate_titles = [str(item) for item in alternates] if isinstance(alternates, list) else []
        score = _candidate_score(query, str(title), alternate_titles)
        candidates.append(
            (
                score,
                ResolvedJournal(str(title), str(issn).upper(), domain, secure_homepage, str(source_id), score),
            )
        )
    candidates.sort(key=lambda item: item[0], reverse=True)
    if not candidates or candidates[0][0] < 0.88:
        raise JournalResolutionError("No sufficiently confident journal match was found")
    if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < 0.05:
        raise JournalResolutionError("The journal candidate is ambiguous; provide an ISSN or official URL")
    return candidates[0][1]


def discover_official_guidance(homepage_url: str, official_domain: str, html: str) -> OfficialGuidance:
    """Identify attributable scope and author-guide links on the official journal site."""
    parser = _LinkParser()
    parser.feed(html)
    scope_candidates: list[tuple[int, str]] = []
    guide_candidates: list[tuple[int, str]] = []
    for href, label in parser.links:
        url = urljoin(homepage_url, href)
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").casefold()
        if parsed.scheme != "https" or hostname != official_domain.casefold():
            continue
        evidence = _normalized(f"{label} {parsed.path}")
        scope_score = sum(
            weight
            for marker, weight in (("aims and scope", 8), ("scope", 5), ("about", 2), ("journal information", 2))
            if marker in evidence
        )
        guide_score = sum(
            weight
            for marker, weight in (
                ("guide for authors", 9),
                ("author guidelines", 9),
                ("submission guidelines", 8),
                ("information for authors", 8),
                ("authors", 2),
                ("submit", 2),
            )
            if marker in evidence
        )
        if scope_score:
            scope_candidates.append((scope_score, url))
        if guide_score:
            guide_candidates.append((guide_score, url))

    def select(candidates: list[tuple[int, str]], kind: str) -> str:
        if not candidates:
            raise JournalResolutionError(f"No official {kind} page was found on the journal homepage")
        candidates.sort(key=lambda item: (-item[0], item[1]))
        if len(candidates) > 1 and candidates[0][0] == candidates[1][0] and candidates[0][1] != candidates[1][1]:
            raise JournalResolutionError(f"Multiple equally supported official {kind} pages were found")
        return candidates[0][1]

    return OfficialGuidance(select(scope_candidates, "scope"), select(guide_candidates, "author guide"))
