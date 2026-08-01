"""Deterministic, evidence-first journal research and profile primitives."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import sqlite3
import time
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from html import unescape
from statistics import median
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException

ClaimClass = Literal["verified fact", "observed pattern", "inference", "expert suggestion"]
OFFICIAL_TYPES = {"official-scope", "official-guide"}
INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "system prompt",
    "developer message",
)


@dataclass(frozen=True)
class ArticleCandidate:
    title: str
    doi: str | None
    issns: tuple[str, ...]
    published: date
    authors: tuple[str, ...]
    canonical_url: str
    open_url: str | None = None
    full_text: str | None = None


@dataclass(frozen=True)
class Evidence:
    source_id: str
    source_type: str
    canonical_url: str | None
    title: str
    identifier: str | None
    published_at: str | None
    retrieved_at: str
    content_hash: str
    locator: str
    access_status: str
    content: str


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", normalized)
    normalized = re.sub(r"^doi:\s*", "", normalized)
    return normalized.rstrip(".") or None


def bibliographic_fingerprint(title: str, authors: tuple[str, ...], year: int) -> str:
    normalized_title = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
    normalized_authors = "|".join(re.sub(r"[^a-z0-9]+", "", author.casefold()) for author in authors[:3])
    return hashlib.sha256(f"{normalized_title}|{normalized_authors}|{year}".encode()).hexdigest()


def same_work(left: ArticleCandidate, right: ArticleCandidate) -> bool:
    left_doi, right_doi = normalize_doi(left.doi), normalize_doi(right.doi)
    if left_doi and right_doi:
        return left_doi == right_doi
    return bibliographic_fingerprint(left.title, left.authors, left.published.year) == bibliographic_fingerprint(
        right.title, right.authors, right.published.year
    )


def select_articles(
    candidates: list[ArticleCandidate],
    journal_issn: str,
    uploaded_dois: set[str],
    uploaded_fingerprints: set[str],
    *,
    today: date | None = None,
) -> tuple[list[ArticleCandidate], list[str]]:
    """Return exactly three eligible works when possible, plus explicit limitations."""
    now = today or datetime.now(UTC).date()
    cutoff = date(now.year - 5, now.month, min(now.day, 28) if now.month == 2 else now.day)
    normalized_upload_dois = {item for value in uploaded_dois if (item := normalize_doi(value))}
    selected: list[ArticleCandidate] = []
    limitations: list[str] = []
    for candidate in sorted(candidates, key=lambda item: item.published, reverse=True):
        doi = normalize_doi(candidate.doi)
        fingerprint = bibliographic_fingerprint(candidate.title, candidate.authors, candidate.published.year)
        if journal_issn not in candidate.issns or not cutoff <= candidate.published <= now:
            continue
        if doi in normalized_upload_dois or fingerprint in uploaded_fingerprints:
            continue
        if any(same_work(candidate, current) for current in selected):
            continue
        selected.append(candidate)
        if len(selected) == 3:
            break
    if len(selected) != 3:
        limitations.append(f"Only {len(selected)} of 3 eligible distinct journal articles were found")
    missing_text = sum(not item.full_text or len(item.full_text.strip()) < 500 for item in selected)
    if missing_text:
        limitations.append(f"{missing_text} discovered articles lack sufficient lawful full text")
    return selected, limitations


def make_evidence(
    source_type: str,
    canonical_url: str | None,
    title: str,
    content: str,
    *,
    identifier: str | None = None,
    published_at: str | None = None,
    locator: str = "document",
    access_status: str = "open",
) -> Evidence:
    if any(marker in content.casefold() for marker in INJECTION_MARKERS):
        raise HTTPException(status_code=422, detail="Source contains prompt-injection-like instructions")
    digest = hashlib.sha256(content.encode()).hexdigest()
    return Evidence(
        source_id=hashlib.sha256(f"{source_type}|{canonical_url or 'private'}|{digest}".encode()).hexdigest()[:32],
        source_type=source_type,
        canonical_url=canonical_url,
        title=title,
        identifier=normalize_doi(identifier),
        published_at=published_at,
        retrieved_at=datetime.now(UTC).isoformat(),
        content_hash=f"sha256:{digest}",
        locator=locator,
        access_status=access_status,
        content=content,
    )


def validate_claim(claim: dict[str, object], evidence_by_id: dict[str, Evidence]) -> None:
    source_ids = claim.get("sourceIds")
    if not isinstance(source_ids, list) or not source_ids:
        raise HTTPException(status_code=422, detail="Every profile claim requires evidence")
    if any(not isinstance(source_id, str) or source_id not in evidence_by_id for source_id in source_ids):
        raise HTTPException(status_code=422, detail="Profile claim references an unknown source")
    claim_class = claim.get("claimClass")
    if claim_class == "verified fact" and not any(
        evidence_by_id[source_id].source_type in OFFICIAL_TYPES
        for source_id in source_ids
        if isinstance(source_id, str)
    ):
        raise HTTPException(status_code=422, detail="Verified journal facts require official evidence")
    if not isinstance(claim.get("locator"), str) or not claim["locator"]:
        raise HTTPException(status_code=422, detail="Every profile claim requires a locator")


def derive_profile(evidence: list[Evidence]) -> tuple[list[dict[str, object]], list[str]]:
    """Derive bounded facts/patterns without an LLM or private raw-text persistence."""
    evidence_by_id = {item.source_id: item for item in evidence}
    official = [item for item in evidence if item.source_type in OFFICIAL_TYPES]
    articles = [item for item in evidence if item.source_type == "article"]
    limitations: list[str] = []
    if {item.source_type for item in official} != OFFICIAL_TYPES:
        limitations.append("Current official scope and author guide are both required")
    if len(articles) < 3:
        limitations.append(
            f"Writing-pattern analysis requires at least 3 supplied full texts; received {len(articles)}"
        )
    claims: list[dict[str, object]] = []
    for source in official:
        claims.append(
            {
                "key": source.source_type,
                "claimClass": "verified fact",
                "summary": f"Current {source.source_type.replace('-', ' ')} snapshot acquired",
                "sourceIds": [source.source_id],
                "locator": source.locator,
                "coverage": "1 official source",
                "confidence": 1.0,
            }
        )
    if len(articles) >= 3:
        sample_size = len(articles)
        article_metrics = [_editorial_metrics(item.content) for item in articles]
        for metric_key, label in (
            ("wordCount", "Extracted article word count"),
            ("meanSentenceWords", "Mean sentence length"),
            ("equationMarkersPerThousandWords", "Equation-marker density per 1,000 words"),
            ("figureMentions", "Figure mentions"),
            ("referenceMarkers", "Numeric reference markers"),
        ):
            values = [float(item[metric_key]) for item in article_metrics]
            claims.append(
                {
                    "key": f"metric:{metric_key}",
                    "claimClass": "observed pattern",
                    "summary": f"{label}: median {median(values):.1f}, range {min(values):.1f}-{max(values):.1f}",
                    "sourceIds": [item.source_id for item in articles],
                    "locator": "full-text deterministic editorial metrics",
                    "coverage": f"{sample_size} of {sample_size} articles",
                    "confidence": 1.0,
                    "value": {"median": median(values), "min": min(values), "max": max(values)},
                }
            )
        section_names = ("abstract", "introduction", "methods", "results", "discussion", "conclusion")
        for section in section_names:
            supporting = [item for item in articles if re.search(rf"\b{section}\b", item.content, re.IGNORECASE)]
            if supporting:
                claims.append(
                    {
                        "key": f"section:{section}",
                        "claimClass": "observed pattern",
                        "summary": f"A labeled {section} section was observed",
                        "sourceIds": [item.source_id for item in supporting],
                        "locator": f"heading:{section}",
                        "coverage": f"{len(supporting)} of {sample_size} articles",
                        "confidence": round(len(supporting) / sample_size, 2),
                    }
                )
        sentence_lengths: list[float] = []
        first_person_sources: list[str] = []
        passive_sources: list[str] = []
        ordered_sources: list[str] = []
        for item in articles:
            sentences = [part for part in re.split(r"[.!?]+", item.content) if part.strip()]
            if sentences:
                sentence_lengths.append(sum(len(sentence.split()) for sentence in sentences) / len(sentences))
            if re.search(r"\b(we|our|ours)\b", item.content, re.IGNORECASE):
                first_person_sources.append(item.source_id)
            if re.search(r"\b(?:was|were|is|are|been)\s+\w+ed\b", item.content, re.IGNORECASE):
                passive_sources.append(item.source_id)
            positions = [item.content.casefold().find(section) for section in section_names]
            if all(position >= 0 for position in positions) and positions == sorted(positions):
                ordered_sources.append(item.source_id)
        if sentence_lengths:
            mean_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            claims.append(
                {
                    "key": "style:mean-sentence-length",
                    "claimClass": "observed pattern",
                    "summary": f"Mean sentence length across the sample was {mean_sentence_length:.1f} words",
                    "sourceIds": [item.source_id for item in articles],
                    "locator": "full-text sentence segmentation",
                    "coverage": f"{len(sentence_lengths)} of {sample_size} articles",
                    "confidence": round(len(sentence_lengths) / sample_size, 2),
                }
            )
        for key, summary, supporting_ids in (
            ("style:first-person", "First-person authorial voice was observed", first_person_sources),
            ("style:passive-marker", "Passive-voice markers were observed", passive_sources),
            ("architecture:canonical-order", "Canonical section ordering was observed", ordered_sources),
        ):
            if supporting_ids:
                claims.append(
                    {
                        "key": key,
                        "claimClass": "observed pattern",
                        "summary": summary,
                        "sourceIds": supporting_ids,
                        "locator": "full-text deterministic pattern scan",
                        "coverage": f"{len(supporting_ids)} of {sample_size} articles",
                        "confidence": round(len(supporting_ids) / sample_size, 2),
                    }
                )
    for claim in claims:
        validate_claim(claim, evidence_by_id)
    return claims, limitations


def _editorial_metrics(text: str) -> dict[str, float]:
    words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", text)
    sentences = [part for part in re.split(r"[.!?]+", text) if len(part.split()) >= 3]
    mean_sentence_words = sum(len(item.split()) for item in sentences) / len(sentences) if sentences else 0.0
    equation_markers = len(re.findall(r"\(\d{1,3}\)", text))
    figure_mentions = len(re.findall(r"\bfig(?:ure)?\.?\s*\d+", text, re.I))
    reference_markers = len(re.findall(r"\[(?:\d+|\d+[–-]\d+)\]", text))
    word_count = max(len(words), 1)
    return {
        "wordCount": float(len(words)),
        "meanSentenceWords": mean_sentence_words,
        "equationMarkersPerThousandWords": equation_markers * 1000 / word_count,
        "figureMentions": float(figure_mentions),
        "referenceMarkers": float(reference_markers),
    }


class JournalProfileRepository:
    """Immutable, optimistic-concurrency journal profile storage."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def migrate(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS journal_profile_versions (
                    id TEXT PRIMARY KEY, journal_issn TEXT NOT NULL, version INTEGER NOT NULL,
                    status TEXT NOT NULL, claims_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    supersedes_id TEXT, UNIQUE(journal_issn, version)
                );
                CREATE TABLE IF NOT EXISTS journal_profile_heads (
                    journal_issn TEXT PRIMARY KEY, version_id TEXT NOT NULL, version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS journal_source_snapshots (
                    profile_version_id TEXT NOT NULL, source_id TEXT NOT NULL, source_type TEXT NOT NULL,
                    content TEXT NOT NULL, content_hash TEXT NOT NULL,
                    PRIMARY KEY(profile_version_id, source_id)
                );
                """
            )

    def publish(
        self,
        journal_issn: str,
        evidence: list[Evidence],
        claims: list[dict[str, object]],
        limitations: list[str],
        expected_version: int,
    ) -> dict[str, object]:
        if limitations:
            raise HTTPException(status_code=409, detail="Degraded research cannot publish a shared profile")
        evidence_by_id = {item.source_id: item for item in evidence}
        for claim in claims:
            validate_claim(claim, evidence_by_id)
        shared_evidence = [{key: value for key, value in asdict(item).items() if key != "content"} for item in evidence]
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            head = connection.execute(
                "SELECT version_id, version FROM journal_profile_heads WHERE journal_issn = ?", (journal_issn,)
            ).fetchone()
            current = int(head[1]) if head else 0
            if current != expected_version:
                raise HTTPException(status_code=409, detail="Journal profile was concurrently updated")
            version = current + 1
            version_id = hashlib.sha256(
                json.dumps([journal_issn, version, shared_evidence, claims], sort_keys=True).encode()
            ).hexdigest()[:32]
            connection.execute(
                "INSERT INTO journal_profile_versions VALUES (?, ?, ?, 'published', ?, ?, ?, ?, ?)",
                (
                    version_id,
                    journal_issn,
                    version,
                    json.dumps(claims, sort_keys=True),
                    json.dumps(shared_evidence, sort_keys=True),
                    "[]",
                    datetime.now(UTC).isoformat(),
                    head[0] if head else None,
                ),
            )
            connection.execute(
                """INSERT INTO journal_profile_heads VALUES (?, ?, ?)
                   ON CONFLICT(journal_issn) DO UPDATE SET version_id=excluded.version_id, version=excluded.version""",
                (journal_issn, version_id, version),
            )
            connection.executemany(
                "INSERT INTO journal_source_snapshots VALUES (?, ?, ?, ?, ?)",
                [
                    (version_id, item.source_id, item.source_type, item.content, item.content_hash)
                    for item in evidence
                    if item.source_type in OFFICIAL_TYPES
                ],
            )
        return self.get(version_id)

    def official_snapshots(self, version_id: str) -> list[dict[str, str]]:
        self.get(version_id)
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT source_id, source_type, content, content_hash
                   FROM journal_source_snapshots WHERE profile_version_id = ? ORDER BY source_type""",
                (version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, version_id: str) -> dict[str, object]:
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM journal_profile_versions WHERE id = ?", (version_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Journal profile version not found")
        return {
            "id": row["id"],
            "journalIssn": row["journal_issn"],
            "version": row["version"],
            "status": row["status"],
            "claims": json.loads(row["claims_json"]),
            "evidence": json.loads(row["evidence_json"]),
            "limitations": json.loads(row["limitations_json"]),
            "createdAt": row["created_at"],
            "supersedesId": row["supersedes_id"],
        }


class PoliteHttpClient:
    """Small bounded HTTP adapter with same-domain enforcement and retry/backoff."""

    def __init__(self, contact_email: str, *, timeout: float = 10, max_bytes: int = 5_000_000) -> None:
        if "@" not in contact_email:
            raise ValueError("An operational contact email is required")
        self.contact_email = contact_email
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.cache: dict[str, bytes] = {}

    def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
        validate_public_https_url(url, allowed_domain)
        if url in self.cache:
            return self.cache[url]
        request = Request(
            url,
            headers={
                "User-Agent": f"ArticleFit/0.1 (mailto:{self.contact_email})",
                "Accept": "application/json,text/html,application/pdf",
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - validated above
                    final_url = response.geturl()
                    validate_public_https_url(final_url, allowed_domain)
                    payload: bytes = response.read(self.max_bytes + 1)
                    if len(payload) > self.max_bytes:
                        raise HTTPException(status_code=413, detail="Remote source exceeds acquisition limit")
                    self.cache[url] = payload
                    return payload
            except HTTPError as error:
                if error.code != 429 or attempt == 2:
                    raise HTTPException(status_code=502, detail=f"Provider returned HTTP {error.code}") from error
                time.sleep(min(float(error.headers.get("Retry-After", "1")), 2))
            except URLError as error:
                raise HTTPException(status_code=502, detail="Provider could not be reached") from error
        raise HTTPException(status_code=502, detail="Provider retry budget exhausted")

    def crossref_candidates(self, issn: str, from_date: str, until_date: str) -> list[ArticleCandidate]:
        query = urlencode(
            {
                "filter": f"from-pub-date:{from_date},until-pub-date:{until_date},type:journal-article",
                "select": "DOI,title,author,published,URL,ISSN",
                "rows": "20",
                "mailto": self.contact_email,
            }
        )
        data = json.loads(self.get(f"https://api.crossref.org/journals/{quote(issn)}/works?{query}"))
        candidates: list[ArticleCandidate] = []
        for item in data.get("message", {}).get("items", []):
            parts = item.get("published", {}).get("date-parts", [[]])[0]
            if not parts:
                continue
            published = date(
                int(parts[0]), int(parts[1]) if len(parts) > 1 else 1, int(parts[2]) if len(parts) > 2 else 1
            )
            authors = tuple(
                " ".join(filter(None, (author.get("given"), author.get("family")))) for author in item.get("author", [])
            )
            candidates.append(
                ArticleCandidate(
                    title=(item.get("title") or [""])[0],
                    doi=item.get("DOI"),
                    issns=tuple(item.get("ISSN", [])),
                    published=published,
                    authors=authors,
                    canonical_url=item.get("URL", ""),
                )
            )
        return candidates

    def openalex_candidates(self, issn: str, from_date: str, until_date: str) -> list[ArticleCandidate]:
        query = urlencode(
            {
                "filter": (
                    f"primary_location.source.issn:{issn},from_publication_date:{from_date},"
                    f"to_publication_date:{until_date},type:article"
                ),
                "per-page": "20",
                "mailto": self.contact_email,
            }
        )
        data = json.loads(self.get(f"https://api.openalex.org/works?{query}"))
        candidates: list[ArticleCandidate] = []
        for item in data.get("results", []):
            published_value = item.get("publication_date")
            location = item.get("primary_location") or {}
            source = location.get("source") or {}
            if not published_value:
                continue
            authors = tuple(
                authorship.get("author", {}).get("display_name", "") for authorship in item.get("authorships", [])
            )
            candidates.append(
                ArticleCandidate(
                    title=item.get("title", ""),
                    doi=item.get("doi"),
                    issns=tuple(source.get("issn", [])),
                    published=date.fromisoformat(published_value),
                    authors=authors,
                    canonical_url=item.get("id", ""),
                    open_url=location.get("pdf_url") or location.get("landing_page_url"),
                )
            )
        return candidates


def validate_public_https_url(url: str, allowed_domain: str | None = None) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    expected = (allowed_domain or hostname).casefold().rstrip(".")
    if parsed.scheme != "https" or not hostname or (hostname != expected and not hostname.endswith(f".{expected}")):
        raise HTTPException(status_code=422, detail="Remote URL is not on the approved HTTPS domain")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as error:
        raise HTTPException(status_code=422, detail="Remote domain could not be resolved") from error
    if any(
        ipaddress.ip_address(address).is_private or ipaddress.ip_address(address).is_loopback for address in addresses
    ):
        raise HTTPException(status_code=422, detail="Private network targets are forbidden")


def html_to_text(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", text))).strip()
