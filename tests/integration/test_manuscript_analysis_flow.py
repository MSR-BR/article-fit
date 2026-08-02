from __future__ import annotations

from fastapi.testclient import TestClient
from journal_matcher_api import main
from journal_matcher_api.foundation import FoundationStore, Principal
from journal_matcher_api.gemini import EditorialResponse, GeminiResult

from tests.conftest import auth
from tests.integration.test_journal_research_flow import FakeProvider, prepare_project


def complete_editorial_proposals(anchor: str) -> list[dict[str, object]]:
    dimensions = [
        "scientific-framing",
        "theory-methodology",
        "validation-robustness",
        "results-analysis",
        "figures-equations",
        "structure",
        "writing",
        "compliance",
        "scientific-framing",
        "validation-robustness",
        "results-analysis",
        "structure",
    ]
    return [
        {
            "anchor": anchor,
            "category": dimension,
            "interventionType": "restructure",
            "priority": "medium",
            "basis": "expert-suggestion",
            "originalText": "Synthetic article",
            "proposedText": "Synthetic article: central result",
            "rationale": "Foreground the principal result and its evidential support.",
            "action": "Revise this dimension after author verification.",
            "journalExpectation": "A concise, evidence-led scientific argument.",
            "referencePattern": "Reference articles connect claims directly to methods and results.",
            "sourceIds": [],
            "scientificImpact": True,
            "authorValidationRequired": True,
        }
        for dimension in dimensions
    ]


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

    class FakeGemini:
        def generate(self, prompt: str) -> GeminiResult:
            assert "UNTRUSTED DATA" in prompt
            return GeminiResult(
                model="test-model",
                response=EditorialResponse.model_validate(
                    {
                        "summary": "The manuscript needs a clearer editorial architecture.",
                        "proposals": complete_editorial_proposals("page:1"),
                        "limitations": ["AI-assisted review requires author validation."],
                    }
                ),
            )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main, "GeminiEditorialClient", FakeGemini)
    ai_review = client.post(f"/v1/analyses/{analysis['id']}/ai-review", headers=auth())
    assert ai_review.status_code == 200, ai_review.text
    ai_analysis = ai_review.json()
    assert any(item.get("origin") == "gemini-editorial-review" for item in ai_analysis["recommendations"])
    assert "AI-assisted review requires author validation." in ai_analysis["limitations"]

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
    assert len(generated.json()["artifacts"]) == 3
    for kind, signature in (
        ("revised-manuscript.docx", b"PK"),
        ("revised-manuscript.pdf", b"%PDF-"),
        ("revision-report.pdf", b"%PDF-"),
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


def test_real_workflow_orchestrator_reaches_downloadable_artifacts(
    client: TestClient, store: FoundationStore, monkeypatch
) -> None:
    openalex_calls: list[str] = []

    class WorkflowProvider(FakeProvider):
        def get(self, url: str, *, allowed_domain: str | None = None) -> bytes:
            if "api.openalex.org/sources" in url:
                openalex_calls.append(url)
                return (
                    b'{"results":[{"id":"https://openalex.org/S1","display_name":"Synthetic Journal",'
                    b'"alternate_titles":[],"issn_l":"1234-567X","homepage_url":"https://example.org/home",'
                    b'"type":"journal"}]}'
                )
            if url == "https://example.org/home":
                return b'<a href="/scope">Aims and Scope</a><a href="/guide">Guide for Authors</a>'
            if url in {"https://example.org/scope", "https://example.org/guide"}:
                raise main.HTTPException(status_code=502, detail="Provider returned HTTP 403")
            return super().get(url, allowed_domain=allowed_domain)

    class WorkflowGemini:
        def generate(self, prompt: str) -> GeminiResult:
            assert "EVIDENCE_PACKAGE_JSON" in prompt
            return GeminiResult(
                model="test-model",
                response=EditorialResponse.model_validate(
                    {
                        "summary": "Editorial review completed.",
                        "proposals": complete_editorial_proposals("paragraph:1"),
                        "limitations": ["AI-assisted editorial review."],
                    }
                ),
            )

    monkeypatch.setenv("JOURNAL_MATCHER_PROVIDER_EMAIL", "research@example.org")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main, "PoliteHttpClient", WorkflowProvider)
    monkeypatch.setattr(main, "GeminiEditorialClient", WorkflowGemini)
    monkeypatch.setattr(main, "validate_public_https_url", lambda url, domain=None: None)
    project_id = prepare_project(client)
    response = client.post(
        f"/v1/projects/{project_id}/run",
        headers=auth(),
        json={
            "idempotencyKey": "workflow-test-001",
            "journalTitle": "Synthetic Journal",
            "journalIssn": "1234-567X",
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "scopeSnapshot": "Official scope for the journal. " + "verified scope evidence " * 30,
            "guideSnapshot": "Official author instructions. " + "verified author guidance " * 30,
        },
    )
    assert response.status_code == 200, response.text
    workflow = response.json()
    assert workflow["state"] == "succeeded"
    assert workflow["stage"] == "artifacts-ready"
    assert len(workflow["artifacts"]) == 3
    assert openalex_calls == []
    assert (
        store.get_project(Principal("invited-pilot-user", "11111111-1111-4111-8111-111111111111"), project_id)[
            "documents"
        ]
        == []
    )
    profile_id = str(workflow["research"]["profileVersion"]["id"])
    assert main.profile_repository(store).official_snapshots(profile_id) == []
    for kind in ("revised-manuscript.docx", "revised-manuscript.pdf", "revision-report.pdf"):
        assert client.get(f"/v1/analyses/{workflow['analysisId']}/artifacts/{kind}", headers=auth()).status_code == 200

    legacy_project_id = prepare_project(client)
    legacy = client.post(
        f"/v1/projects/{legacy_project_id}/run",
        headers=auth(),
        json={
            "idempotencyKey": "workflow-legacy-001",
            "scopeUrl": "https://example.org/scope",
            "guideUrl": "https://example.org/guide",
            "scopeSnapshot": "Official scope for the journal. " + "verified scope evidence " * 30,
            "guideSnapshot": "Official author instructions. " + "verified author guidance " * 30,
        },
    )
    assert legacy.status_code == 200, legacy.text
    assert len(openalex_calls) == 1
