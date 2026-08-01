import pytest
from journal_matcher_api.journal_resolution import (
    JournalResolutionError,
    discover_official_guidance,
    resolve_openalex_sources,
)


def source(title: str, issn: str, homepage: str, source_id: str) -> dict[str, object]:
    return {
        "id": source_id,
        "display_name": title,
        "alternate_titles": [],
        "issn_l": issn,
        "homepage_url": homepage,
        "type": "journal",
    }


def test_resolves_exact_user_supplied_journal_title() -> None:
    resolved = resolve_openalex_sources(
        "Physical Review Letters",
        {"results": [source("Physical Review Letters", "0031-9007", "https://journals.aps.org/prl", "S1")]},
    )
    assert resolved.issn == "0031-9007"
    assert resolved.official_domain == "journals.aps.org"
    assert resolved.confidence == 1.0


def test_upgrades_provider_homepage_to_https_before_verification() -> None:
    resolved = resolve_openalex_sources(
        "Physical Review Letters",
        {"results": [source("Physical Review Letters", "0031-9007", "http://journals.aps.org/prl/", "S1")]},
    )
    assert resolved.homepage_url == "https://journals.aps.org/prl/"


def test_rejects_ambiguous_title_and_requests_stronger_identifier() -> None:
    payload = {
        "results": [
            source("Journal of Physics", "1111-1111", "https://one.example/journal", "S1"),
            source("Journal of Physics", "2222-2222", "https://two.example/journal", "S2"),
        ]
    }
    with pytest.raises(JournalResolutionError, match="ambiguous"):
        resolve_openalex_sources("Journal of Physics", payload)


def test_rejects_weak_or_non_official_metadata() -> None:
    payload = {"results": [source("Unrelated Venue", "1111-1111", "http://openalex.org/source", "S1")]}
    with pytest.raises(JournalResolutionError, match="No sufficiently confident"):
        resolve_openalex_sources("Target Journal", payload)


def test_discovers_scope_and_author_guide_only_on_official_domain() -> None:
    html = """
    <a href="https://attacker.example/guide-for-authors">Guide for Authors</a>
    <a href="/journal/about">Aims and Scope</a>
    <a href="/journal/authors">Information for Authors</a>
    """
    result = discover_official_guidance("https://journal.example/home", "journal.example", html)
    assert result.scope_url == "https://journal.example/journal/about"
    assert result.guide_url == "https://journal.example/journal/authors"


def test_guidance_discovery_fails_when_official_link_is_missing() -> None:
    with pytest.raises(JournalResolutionError, match="author guide"):
        discover_official_guidance(
            "https://journal.example/home", "journal.example", '<a href="/scope">Aims and Scope</a>'
        )
