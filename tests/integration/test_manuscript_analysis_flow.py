from __future__ import annotations

from fastapi.testclient import TestClient
from journal_matcher_api import main
from journal_matcher_api.foundation import FoundationStore

from tests.conftest import auth
from tests.integration.test_journal_research_flow import FakeProvider, prepare_project


def create_profile(client: TestClient, project_id: str) -> str:
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
    return str(response.json()["profileVersion"]["id"])


def test_analysis_review_artifacts_and_tenant_isolation(
    client: TestClient, store: FoundationStore, monkeypatch
) -> None:
    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setattr(main, "PoliteHttpClient", FakeProvider)
    project_id = prepare_project(client)
    profile_id = create_profile(client, project_id)
    response = client.post(f"/v1/projects/{project_id}/analyses", headers=auth(), json={"profileVersionId": profile_id})
    assert response.status_code == 201, response.text
    analysis = response.json()
    assert analysis["status"] == "review"
    assert analysis["limitations"]
    assert analysis["rules"]
    recommendation = next(item for item in analysis["recommendations"] if item["scientificImpact"])

    blocked = client.post(
        f"/v1/analyses/{analysis['id']}/recommendations/{recommendation['id']}/decision",
        headers=auth(),
        json={"decision": "accepted"},
    )
    assert blocked.status_code == 409
    modified = client.post(
        f"/v1/analyses/{analysis['id']}/recommendations/{recommendation['id']}/decision",
        headers=auth(),
        json={"decision": "modified", "modifiedText": "Author-verified statement."},
    )
    assert modified.status_code == 200

    generated = client.post(f"/v1/analyses/{analysis['id']}/artifacts", headers=auth())
    assert generated.status_code == 201, generated.text
    assert len(generated.json()["artifacts"]) == 4
    for kind, signature in (
        ("revised-manuscript.docx", b"PK"),
        ("revised-manuscript.pdf", b"%PDF-"),
        ("revision-report.pdf", b"%PDF-"),
        ("provenance-manifest.json", b"{"),
    ):
        download = client.get(f"/v1/analyses/{analysis['id']}/artifacts/{kind}", headers=auth())
        assert download.status_code == 200
        assert download.content.startswith(signature)

    unauthorized = client.get(
        f"/v1/analyses/{analysis['id']}",
        headers={
            "Authorization": "Bearer local-invite-token",
            "X-Workspace-Id": "22222222-2222-4222-8222-222222222222",
        },
    )
    assert unauthorized.status_code == 404
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in store.object_root.rglob("*") if path.is_file())
    assert client.get(f"/v1/analyses/{analysis['id']}/artifacts/revision-report.pdf").status_code == 401
    assert client.delete(f"/v1/projects/{project_id}", headers=auth()).status_code == 204
    assert not [path for path in store.object_root.rglob("*") if path.is_file()]
    assert client.get(f"/v1/analyses/{analysis['id']}", headers=auth()).status_code == 404
