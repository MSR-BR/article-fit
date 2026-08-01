from __future__ import annotations

from fastapi.testclient import TestClient
from journal_matcher_api.foundation import FoundationStore

from tests.conftest import WORKSPACE_B, auth, synthetic_docx, synthetic_pdf


def create_project(client: TestClient) -> str:
    response = client.post("/v1/projects", headers=auth(), json={"journalCandidate": "Synthetic Journal"})
    assert response.status_code == 201
    return str(response.json()["id"])


def upload(client: TestClient, project_id: str, slot: str, content: bytes, media_type: str) -> None:
    response = client.put(
        f"/v1/projects/{project_id}/documents/{slot}?filename={slot}.bin",
        headers={**auth(), "Content-Type": "application/octet-stream", "X-Document-Media-Type": media_type},
        content=content,
    )
    assert response.status_code == 200, response.text


def test_complete_ingestion_is_idempotent_and_private(client: TestClient, store: FoundationStore) -> None:
    project_id = create_project(client)
    journal = client.put(
        f"/v1/projects/{project_id}/journal",
        headers=auth(),
        json={"title": "Synthetic Journal", "issn": "1234-567X", "officialDomain": "example.org"},
    )
    assert journal.status_code == 200

    upload(
        client,
        project_id,
        "manuscript",
        synthetic_docx(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    for slot in ("reference-1", "reference-2", "reference-3"):
        upload(client, project_id, slot, synthetic_pdf(slot), "application/pdf")

    ready = client.get(f"/v1/projects/{project_id}", headers=auth()).json()
    assert ready["readyForResearch"] is True
    assert len(ready["documents"]) == 4

    first = client.post(
        f"/v1/projects/{project_id}/jobs",
        headers=auth(),
        json={"idempotencyKey": "ingest-request-001"},
    )
    second = client.post(
        f"/v1/projects/{project_id}/jobs",
        headers=auth(),
        json={"idempotencyKey": "ingest-request-001"},
    )
    assert first.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["state"] == "succeeded"

    unauthorized = client.get(f"/v1/projects/{project_id}", headers=auth(WORKSPACE_B))
    assert unauthorized.status_code == 404

    object_paths = [path for path in store.object_root.rglob("*") if path.is_file()]
    assert len(object_paths) == 4
    deleted = client.delete(f"/v1/projects/{project_id}", headers=auth())
    assert deleted.status_code == 204
    assert not [path for path in store.object_root.rglob("*") if path.is_file()]


def test_job_requires_four_documents_and_confirmed_journal(client: TestClient) -> None:
    project_id = create_project(client)
    response = client.post(
        f"/v1/projects/{project_id}/jobs",
        headers=auth(),
        json={"idempotencyKey": "incomplete-job"},
    )
    assert response.status_code == 409
    assert "exactly one manuscript" in response.json()["detail"]


def test_duplicate_slot_authentication_and_completed_cancel_fail_safely(client: TestClient) -> None:
    assert client.post("/v1/projects", json={"journalCandidate": "Journal"}).status_code == 401
    invalid_workspace = client.post(
        "/v1/projects",
        headers=auth("not-a-uuid"),
        json={"journalCandidate": "Journal"},
    )
    assert invalid_workspace.status_code == 400

    project_id = create_project(client)
    upload(client, project_id, "reference-1", synthetic_pdf(), "application/pdf")
    duplicate = client.put(
        f"/v1/projects/{project_id}/documents/reference-1?filename=again.pdf",
        headers={
            **auth(),
            "Content-Type": "application/octet-stream",
            "X-Document-Media-Type": "application/pdf",
        },
        content=synthetic_pdf("duplicate"),
    )
    assert duplicate.status_code == 409
