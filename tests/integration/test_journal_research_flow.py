from __future__ import annotations

import json
from datetime import date

from fastapi.testclient import TestClient
from journal_matcher_api import main
from journal_matcher_api.foundation import FoundationStore
from journal_matcher_api.journal_research import ArticleCandidate

from tests.conftest import auth, synthetic_docx, synthetic_pdf
from tests.integration.test_ingestion_flow import create_project, upload


class FakeProvider:
    def __init__(self, contact_email: str) -> None:
        self.contact_email = contact_email

    def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
        if "api.unpaywall.org" in url:
            number = url.split("article.", 1)[1].split("?", 1)[0]
            return json.dumps({"best_oa_location": {"url_for_pdf": f"https://repository.example/{number}"}}).encode()
        if "repository.example" in url:
            return (
                "<h1>Abstract</h1><h2>Introduction</h2><h2>Methods</h2><h2>Results</h2>"
                "<h2>Discussion</h2><h2>Conclusion</h2>" + " evidence" * 120
            ).encode()
        return (
            "<h1>Official journal information</h1> Abstract must not exceed 250 words. "
            "Include a data availability statement and a competing interests statement." + " current guidance" * 100
        ).encode()

    def crossref_candidates(self, issn: str, from_date: str, until_date: str) -> list[ArticleCandidate]:
        return [
            ArticleCandidate(
                title=f"Discovered article {index}",
                doi=f"10.1000/article.{index}",
                issns=(issn,),
                published=date(2026, index, 1),
                authors=("Research Author",),
                canonical_url=f"https://doi.org/10.1000/article.{index}",
            )
            for index in range(1, 4)
        ]


def test_resolve_journal_returns_attributable_official_pages(client: TestClient, monkeypatch) -> None:
    class ResolutionProvider:
        def __init__(self, contact_email: str) -> None:
            assert contact_email == "research@example.org"

        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if "api.openalex.org/sources" in url:
                return json.dumps(
                    {
                        "results": [
                            {
                                "id": "https://openalex.org/S123",
                                "display_name": "Physical Review Letters",
                                "alternate_titles": ["PRL"],
                                "issn_l": "0031-9007",
                                "homepage_url": "https://journals.aps.org/prl",
                                "type": "journal",
                            }
                        ]
                    }
                ).encode()
            assert allowed_domain == "journals.aps.org"
            return b'<a href="/prl/about">Aims and Scope</a><a href="/prl/authors">Information for Authors</a>'

    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", ResolutionProvider)
    response = client.post("/v1/journals/resolve", headers=auth(), json={"candidate": "Physical Review Letters"})
    assert response.status_code == 200, response.text
    resolved = response.json()
    assert resolved["issn"] == "0031-9007"
    assert resolved["scopeUrl"] == "https://journals.aps.org/prl/about"
    assert resolved["guideUrl"] == "https://journals.aps.org/prl/authors"
    assert resolved["evidence"]["provider"] == "OpenAlex"
    assert client.post("/v1/journals/resolve", json={"candidate": "Physical Review Letters"}).status_code == 401


def test_resolve_journal_follows_official_navigation_page(client: TestClient, monkeypatch) -> None:
    class NavigationProvider:
        def __init__(self, _contact_email: str) -> None:
            pass

        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if "api.openalex.org/sources" in url:
                return json.dumps(
                    {
                        "results": [
                            {
                                "id": "https://openalex.org/S123",
                                "display_name": "Physical Review Letters",
                                "alternate_titles": ["PRL"],
                                "issn_l": "0031-9007",
                                "homepage_url": "https://journals.aps.org/prl",
                                "type": "journal",
                            }
                        ]
                    }
                ).encode()
            assert allowed_domain == "journals.aps.org"
            if url == "https://journals.aps.org/prl":
                return b'<a href="/prl/journal-info">Journal information</a>'
            return b'<a href="/prl/about">Scope</a><a href="/prl/authors">Guide for Authors</a>'

    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", NavigationProvider)

    response = client.post("/v1/journals/resolve", headers=auth(), json={"candidate": "Physical Review Letters"})

    assert response.status_code == 200
    assert response.json()["scopeUrl"] == "https://journals.aps.org/prl/about"
    assert response.json()["guideUrl"] == "https://journals.aps.org/prl/authors"


def test_resolve_journal_uses_public_memory_when_publisher_blocks(client: TestClient, monkeypatch) -> None:
    class BlockingProvider:
        def __init__(self, _contact_email: str) -> None:
            pass

        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if "api.openalex.org/sources" in url:
                return json.dumps(
                    {
                        "results": [
                            {
                                "id": "https://openalex.org/S123",
                                "display_name": "Physical Review Letters",
                                "alternate_titles": ["PRL"],
                                "issn_l": "0031-9007",
                                "homepage_url": "https://journals.aps.org/prl",
                                "type": "journal",
                            }
                        ]
                    }
                ).encode()
            raise main.HTTPException(status_code=502, detail="Provider returned HTTP 403")

    class CachedProfiles:
        def migrate(self) -> None:
            pass

        def current(self, _issn: str) -> dict[str, object]:
            return {
                "evidence": [
                    {
                        "source_type": "official-scope",
                        "canonical_url": "https://journals.aps.org/prl/about",
                    },
                    {
                        "source_type": "official-guide",
                        "canonical_url": "https://journals.aps.org/prl/authors",
                    },
                ]
            }

    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", BlockingProvider)
    monkeypatch.setattr(main, "profile_repository", lambda _store: CachedProfiles())
    monkeypatch.setattr(main, "validate_public_https_url", lambda *_args: None)

    response = client.post("/v1/journals/resolve", headers=auth(), json={"candidate": "Physical Review Letters"})

    assert response.status_code == 200
    assert response.json()["scopeUrl"] == "https://journals.aps.org/prl/about"
    assert response.json()["guideUrl"] == "https://journals.aps.org/prl/authors"


def prepare_project(client: TestClient) -> str:
    project_id = create_project(client)
    response = client.put(
        f"/v1/projects/{project_id}/journal",
        headers=auth(),
        json={"title": "Synthetic Journal", "issn": "1234-567X", "officialDomain": "example.org"},
    )
    assert response.status_code == 200
    upload(
        client,
        project_id,
        "manuscript",
        synthetic_docx(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    for slot in ("reference-1", "reference-2", "reference-3"):
        upload(client, project_id, slot, synthetic_pdf(slot), "application/pdf")
    return project_id


def test_research_publishes_only_complete_evidence_profile(
    client: TestClient, store: FoundationStore, monkeypatch
) -> None:
    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", FakeProvider)
    project_id = prepare_project(client)
    response = client.post(
        f"/v1/projects/{project_id}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "expectedProfileVersion": 0,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "complete"
    assert len(result["selectedArticles"]) == 3
    assert result["limitations"] == []
    assert result["warnings"] == []
    assert result["profileVersion"]["version"] == 1
    assert all(source["canonicalUrl"] for source in result["sources"])
    version_id = result["profileVersion"]["id"]
    selected_version = client.get(f"/v1/journal-profiles/{version_id}", headers=auth())
    assert selected_version.status_code == 200
    assert selected_version.json()["version"] == 1

    with store.connect() as connection:
        stored = connection.execute("SELECT evidence_json FROM journal_profile_versions").fetchone()[0]
    assert "reference-1 methods" not in stored
    assert "content" not in json.loads(stored)[0]

    conflict = client.post(
        f"/v1/projects/{project_id}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "expectedProfileVersion": 0,
        },
    )
    assert conflict.status_code == 409


def test_research_requires_provider_contact_and_complete_ingestion(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("JOURNAL_MATCHER_PROVIDER_EMAIL", raising=False)
    project_id = create_project(client)
    response = client.post(
        f"/v1/projects/{project_id}/research",
        headers=auth(),
        json={"scopeUrl": "https://example.org/scope", "guideUrl": "https://example.org/guide"},
    )
    assert response.status_code == 409


def test_browser_assisted_official_snapshot_is_auditable_fallback(
    client: TestClient, store: FoundationStore, monkeypatch
) -> None:
    class BlockedOfficialProvider(FakeProvider):
        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if allowed_domain:
                raise main.HTTPException(status_code=502, detail="Provider returned HTTP 403")
            return super().get(url, allowed_domain=allowed_domain)

    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", BlockedOfficialProvider)
    monkeypatch.setattr(main, "validate_public_https_url", lambda url, domain=None: None)
    project_id = prepare_project(client)
    official_text = "Official journal scope and author guidance. " + "verified evidence " * 60
    response = client.post(
        f"/v1/projects/{project_id}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "scopeSnapshot": official_text,
            "guideSnapshot": official_text,
            "assistedCaptureConfirmed": True,
        },
    )
    assert response.status_code == 200, response.text
    official_sources = [source for source in response.json()["sources"] if source["sourceType"].startswith("official")]
    assert {source["accessStatus"] for source in official_sources} == {"browser-assisted"}


def test_blocked_official_pages_reuse_latest_historical_snapshots(
    client: TestClient, store: FoundationStore, monkeypatch
) -> None:
    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", FakeProvider)

    first_project = prepare_project(client)
    first = client.post(
        f"/v1/projects/{first_project}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "expectedProfileVersion": 0,
        },
    )
    assert first.status_code == 200, first.text

    second_project = prepare_project(client)
    second = client.post(
        f"/v1/projects/{second_project}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "expectedProfileVersion": 1,
        },
    )
    assert second.status_code == 200, second.text
    repository = main.profile_repository(store)
    repository.delete_snapshots(str(second.json()["profileVersion"]["id"]))

    class BlockedOfficialProvider(FakeProvider):
        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if allowed_domain:
                raise main.HTTPException(status_code=502, detail="Provider returned HTTP 403")
            return super().get(url, allowed_domain=allowed_domain)

    monkeypatch.setattr(main, "PoliteHttpClient", BlockedOfficialProvider)
    third_project = prepare_project(client)
    response = client.post(
        f"/v1/projects/{third_project}/research",
        headers=auth(),
        json={
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "expectedProfileVersion": 2,
        },
    )

    assert response.status_code == 200, response.text
    official_sources = [source for source in response.json()["sources"] if source["sourceType"].startswith("official")]
    assert {source["accessStatus"] for source in official_sources} == {"cached-official"}
    assert any("publisher blocked automated access" in warning for warning in response.json()["warnings"])
