from __future__ import annotations

import pytest
from fastapi import HTTPException
from journal_matcher_api.foundation import Principal
from journal_matcher_api.hosted import (
    HostedAnalysisRepository,
    HostedFoundationStore,
    HostedJournalProfileRepository,
)
from journal_matcher_api.journal_research import make_evidence
from journal_matcher_api.manuscript_analysis import stable_id

WORKSPACE = "11111111-1111-4111-8111-111111111111"
PRINCIPAL = Principal("pilot-user", WORKSPACE)


class ScriptedClient:
    def __init__(self, responses: list[object], rpc_responses: list[object] | None = None) -> None:
        self.responses = responses
        self.rpc_responses = rpc_responses or []
        self.calls: list[tuple[str, str]] = []
        self.table_requests: list[tuple[str, str, dict[str, object]]] = []
        self.uploads: list[tuple[str, str]] = []
        self.deletions: list[tuple[str, list[str]]] = []
        self.rpcs: list[tuple[str, str]] = []

    def table(self, name: str, *, method: str = "GET", **kwargs: object) -> object:
        self.calls.append((name, method))
        self.table_requests.append((name, method, kwargs))
        if not self.responses:
            raise AssertionError(f"Unexpected table call: {name} {method}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def upload(self, bucket: str, object_key: str, content: bytes, media_type: str) -> None:
        del content, media_type
        self.uploads.append((bucket, object_key))

    def download(self, bucket: str, object_key: str) -> bytes:
        return f"{bucket}:{object_key}".encode()

    def delete_objects(self, bucket: str, object_keys: list[str]) -> None:
        self.deletions.append((bucket, object_keys))

    def rpc(self, function: str, payload: dict[str, object], *, schema: str = "public") -> object:
        del payload
        self.rpcs.append((function, schema))
        return self.rpc_responses.pop(0) if self.rpc_responses else 1


def project_row(*, confirmed: bool = False) -> dict[str, object]:
    return {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "journal_candidate": "Physical Review Letters",
        "journal_title": "Physical Review Letters" if confirmed else None,
        "journal_issn": "0031-9007" if confirmed else None,
        "journal_domain": "journals.aps.org" if confirmed else None,
        "journal_confirmed_at": "2026-08-01T00:00:00+00:00" if confirmed else None,
        "created_at": "2026-08-01T00:00:00+00:00",
    }


def job_row(state: str = "queued") -> dict[str, object]:
    return {
        "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "project_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "state": state,
        "stage": "awaiting-worker",
        "progress": 0,
        "error_code": None,
        "retry_eligible": False,
        "updated_at": "2026-08-01T00:00:00+00:00",
    }


def run_row() -> dict[str, object]:
    return {
        "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "project_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "profile_version_id": "dddddddddddddddddddddddddddddddd",
        "status": "review",
        "limitations_json": [],
        "created_at": "2026-08-01T00:00:00+00:00",
    }


def analysis_get_responses(
    recommendations: list[dict[str, object]] | None = None,
    decisions: list[dict[str, object]] | None = None,
) -> list[object]:
    recommendation_rows = [{"id": item["id"], "recommendation_json": item} for item in (recommendations or [])]
    values: list[object] = [[run_row()], [], recommendation_rows]
    if recommendation_rows:
        values.append(decisions or [])
    values.append([])
    return values


def test_project_create_confirm_and_missing_paths() -> None:
    created = project_row()
    client = ScriptedClient([None, None, None, [created], [], [created], None, None, [project_row(confirmed=True)], []])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]

    project = store.create_project(PRINCIPAL, "Physical Review Letters")
    confirmed = store.confirm_journal(
        PRINCIPAL, str(project["id"]), "Physical Review Letters", "0031-9007", "journals.aps.org"
    )

    assert confirmed["readyForResearch"] is False
    missing = HostedFoundationStore(ScriptedClient([[]]))  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="Project not found"):
        missing.get_project(PRINCIPAL, "missing")


def test_document_storage_and_private_download(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "journal_matcher_api.hosted.validate_and_extract",
        lambda *args: {
            "media_type": "application/pdf",
            "quality": 1.0,
            "segments": [{"anchor": "page:1", "text": "evidence"}],
        },
    )
    client = ScriptedClient([[project_row()], None, None, [project_row()], []])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    store.store_document(PRINCIPAL, str(project_row()["id"]), "reference-1", "paper.pdf", "application/pdf", b"pdf")

    key = client.uploads[0][1]
    assert store.read_private_object(PRINCIPAL, key).startswith(b"manuscripts:")
    with pytest.raises(HTTPException, match="Private object"):
        store.read_private_object(PRINCIPAL, f"other-workspace/{key}")


def test_document_failure_removes_uploaded_object(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "journal_matcher_api.hosted.validate_and_extract",
        lambda *args: {"media_type": "application/pdf", "quality": 1.0, "segments": []},
    )
    client = ScriptedClient([[project_row()], HTTPException(status_code=409, detail="duplicate")])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="duplicate"):
        store.store_document(PRINCIPAL, str(project_row()["id"]), "reference-1", "p.pdf", "application/pdf", b"x")
    assert client.deletions[0][0] == "manuscripts"


def test_job_queue_idempotency_cancel_and_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    client = ScriptedClient([[], [job_row()], [job_row()], None, [job_row("cancelled")]])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    monkeypatch.setattr(store, "get_project", lambda *args: {"readyForResearch": True})
    monkeypatch.setattr(store, "audit", lambda *args, **kwargs: None)
    cleaned_projects: list[str] = []
    monkeypatch.setattr(
        store,
        "delete_source_documents",
        lambda principal, project_id: cleaned_projects.append(project_id) or 0,
    )

    queued = store.start_job(PRINCIPAL, str(project_row()["id"]), "request-key")
    cancelled = store.cancel_job(PRINCIPAL, str(queued["id"]))

    assert queued["state"] == "queued"
    assert cancelled["state"] == "cancelled"
    assert cleaned_projects == [str(project_row()["id"])]
    assert client.rpcs == [("send", "pgmq_public")]
    missing = HostedFoundationStore(ScriptedClient([[]]))  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="Job not found"):
        missing.get_job(PRINCIPAL, "missing")


def test_worker_queue_and_job_state_boundaries() -> None:
    queued = job_row()
    queued["attempt_count"] = 0
    running = {**queued, "state": "running", "stage": "journal-research", "progress": 10, "attempt_count": 1}
    client = ScriptedClient([[queued], [queued], [running]], rpc_responses=[[{"msg_id": 9, "message": {}}], True])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]

    assert store.read_queue() == [{"msg_id": 9, "message": {}}]
    assert store.worker_job(str(queued["id"])) == queued
    assert (
        store.update_worker_job(
            str(queued["id"]), state="running", stage="journal-research", progress=10, increment_attempt=True
        )
        == running
    )
    store.delete_queue_message(9)
    assert client.rpcs == [("read", "pgmq_public"), ("delete", "pgmq_public")]


def test_reference_and_manuscript_records(monkeypatch: pytest.MonkeyPatch) -> None:
    client = ScriptedClient(
        [
            [{"segments_json": [{"text": "reference text"}]}],
            [
                {
                    "id": "doc",
                    "filename": "draft.docx",
                    "media_type": "application/pdf",
                    "content_hash": "sha256:abc",
                    "object_key": f"{WORKSPACE}/project/doc",
                    "segments_json": [{"anchor": "page:1", "text": "manuscript"}],
                }
            ],
        ]
    )
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    monkeypatch.setattr(store, "_project_row", lambda *args: project_row())
    assert store.reference_texts(PRINCIPAL, "project") == ["reference text"]
    assert store.manuscript_record(PRINCIPAL, "project")["text"] == "manuscript"


def test_profile_publish_and_snapshots() -> None:
    guide = make_evidence("official-guide", "https://journals.aps.org/guide", "Guide", "guide text")
    scope = make_evidence("official-scope", "https://journals.aps.org/scope", "Scope", "scope text")
    claim = {
        "key": "official-guide",
        "claimClass": "verified fact",
        "summary": "guide",
        "sourceIds": [guide.source_id],
        "locator": "page",
    }
    stored = {
        "id": "profile",
        "journal_issn": "0031-9007",
        "version": 1,
        "status": "published",
        "claims_json": [claim],
        "evidence_json": [],
        "limitations_json": [],
        "created_at": "now",
        "supersedes_id": None,
    }
    client = ScriptedClient(
        [
            [],
            None,
            None,
            None,
            [stored],
            [stored],
            [{"source_id": guide.source_id}],
            [{"version": 1}],
            None,
        ]
    )
    repository = HostedJournalProfileRepository(client)  # type: ignore[arg-type]

    assert repository.publish("0031-9007", [guide, scope], [claim], [], 0)["version"] == 1
    assert repository.official_snapshots("profile") == [{"source_id": guide.source_id}]
    assert repository.current_version("0031-9007") == 1
    repository.delete_snapshots("profile")
    assert ("journal_source_snapshots", "DELETE") in client.calls
    with pytest.raises(HTTPException, match="Degraded"):
        repository.publish("0031-9007", [guide], [claim], ["missing"], 1)


def test_profile_finds_historical_official_snapshots() -> None:
    client = ScriptedClient(
        [
            [{"id": "new", "version": 2}, {"id": "old", "version": 1}],
            [],
            [
                {
                    "source_id": "scope",
                    "source_type": "official-scope",
                    "content": "historical scope",
                    "content_hash": "sha256:scope",
                },
                {
                    "source_id": "guide",
                    "source_type": "official-guide",
                    "content": "historical guide",
                    "content_hash": "sha256:guide",
                },
            ],
        ]
    )
    repository = HostedJournalProfileRepository(client)  # type: ignore[arg-type]

    snapshots = repository.latest_official_snapshots("0031-9007")

    assert {item["source_type"] for item in snapshots} == {"official-scope", "official-guide"}
    assert client.calls == [
        ("journal_profile_versions", "GET"),
        ("journal_source_snapshots", "GET"),
        ("journal_source_snapshots", "GET"),
    ]


def test_analysis_create_get_review_and_decision() -> None:
    recommendation = {
        "id": "recommendation-1",
        "scientificImpact": False,
        "decision": "pending",
    }
    scoped_recommendation = {
        **recommendation,
        "id": stable_id(str(run_row()["id"]), "recommendation", recommendation["id"]),
    }
    responses: list[object] = [
        [],
        None,
        *analysis_get_responses(),
        *analysis_get_responses(),
        None,
        None,
        *analysis_get_responses([scoped_recommendation]),
        *analysis_get_responses([scoped_recommendation]),
        None,
        *analysis_get_responses(
            [scoped_recommendation],
            [
                {
                    "recommendation_id": scoped_recommendation["id"],
                    "decision": "modified",
                    "modified_text": "new",
                    "created_at": "now",
                }
            ],
        ),
    ]
    client = ScriptedClient(responses)
    repository = HostedAnalysisRepository(client)  # type: ignore[arg-type]
    created = repository.create(PRINCIPAL, str(project_row()["id"]), "profile", "sha256:x", {}, [], [], [])
    reviewed = repository.add_ai_review(PRINCIPAL, str(created["id"]), [recommendation], ["expert review"])
    decided = repository.decide(PRINCIPAL, str(created["id"]), str(scoped_recommendation["id"]), "modified", "new")

    assert reviewed["id"] == created["id"]
    assert decided["recommendations"][0]["decision"] == "modified"  # type: ignore[index]


def test_analysis_create_repairs_partial_run_with_analysis_scoped_children() -> None:
    project_id = str(project_row()["id"])
    analysis_id = stable_id(WORKSPACE, project_id, "profile", "sha256:x")
    rule = {"id": "shared-rule", "key": "article-word-limit"}
    recommendation = {"id": "shared-recommendation", "decision": "pending"}
    scoped_rule = {**rule, "id": stable_id(analysis_id, "guide-rule", rule["id"])}
    scoped_recommendation = {
        **recommendation,
        "id": stable_id(analysis_id, "recommendation", recommendation["id"]),
    }
    stored_run = {**run_row(), "id": analysis_id}
    client = ScriptedClient(
        [
            [{"id": analysis_id}],
            None,
            None,
            [stored_run],
            [{"rule_json": scoped_rule}],
            [{"id": scoped_recommendation["id"], "recommendation_json": scoped_recommendation}],
            [],
            [],
        ]
    )
    repository = HostedAnalysisRepository(client)  # type: ignore[arg-type]

    repaired = repository.create(
        PRINCIPAL,
        project_id,
        "profile",
        "sha256:x",
        {},
        [rule],
        [recommendation],
        [],
    )

    assert repaired["rules"] == [scoped_rule]
    assert repaired["recommendations"] == [scoped_recommendation]
    assert ("analysis_runs", "POST") not in client.calls
    child_requests = [request for request in client.table_requests if request[1] == "POST"]
    assert [request[0] for request in child_requests] == ["guide_rules", "recommendations"]
    assert all(request[2]["prefer"] == "resolution=ignore-duplicates" for request in child_requests)


def test_analysis_artifact_storage_and_lookup() -> None:
    client = ScriptedClient(
        [
            *analysis_get_responses(),
            None,
            None,
            *analysis_get_responses(),
            *analysis_get_responses(),
            [{"object_key": f"{WORKSPACE}/artifacts/a/report.pdf"}],
        ]
    )
    repository = HostedAnalysisRepository(client)  # type: ignore[arg-type]
    repository.store_artifacts(PRINCIPAL, str(run_row()["id"]), {"report.pdf": b"%PDF-report"}, {"ok": True})
    key = repository.artifact_key(PRINCIPAL, str(run_row()["id"]), "report.pdf")

    assert key.endswith("report.pdf")
    assert client.uploads[0][0] == "artifacts"


def test_hosted_delete_and_retention(monkeypatch: pytest.MonkeyPatch) -> None:
    object_key = f"{WORKSPACE}/project/document"
    client = ScriptedClient([[project_row()], [{"object_key": object_key}], [], None, None, None])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    store.delete_project(PRINCIPAL, str(project_row()["id"]))
    assert client.deletions == [("manuscripts", [object_key])]

    expired = ScriptedClient([[{"id": "old", "workspace_id": WORKSPACE, "owner_id": "pilot-user"}], None])
    retention_store = HostedFoundationStore(expired)  # type: ignore[arg-type]
    deleted: list[str] = []
    monkeypatch.setattr(retention_store, "delete_project", lambda principal, project_id: deleted.append(project_id))
    assert retention_store.purge_expired() == 1
    assert deleted == ["old"]
    assert ("audit_events", "DELETE") in expired.calls


def test_hosted_source_documents_are_hard_deleted() -> None:
    object_key = f"{WORKSPACE}/project/source.pdf"
    client = ScriptedClient([[project_row()], [{"object_key": object_key}], None, None])
    store = HostedFoundationStore(client)  # type: ignore[arg-type]

    assert store.delete_source_documents(PRINCIPAL, str(project_row()["id"])) == 1
    assert client.deletions == [("manuscripts", [object_key])]
    assert ("documents", "DELETE") in client.calls


def test_hosted_project_delete_prunes_unreferenced_superseded_profile() -> None:
    profile_id = str(run_row()["profile_version_id"])
    client = ScriptedClient(
        [
            [project_row()],
            [],
            [{"id": run_row()["id"], "profile_version_id": profile_id}],
            [],
            [],
            None,
            None,
            None,
            None,
            None,
            [],
            [],
            None,
            None,
            None,
            None,
            None,
        ]
    )
    store = HostedFoundationStore(client)  # type: ignore[arg-type]

    store.delete_project(PRINCIPAL, str(project_row()["id"]))

    profile_calls = [call for call in client.calls if call[0] == "journal_profile_versions"]
    assert profile_calls == [("journal_profile_versions", "PATCH"), ("journal_profile_versions", "DELETE")]


def test_hosted_job_guards_and_profile_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    store = HostedFoundationStore(ScriptedClient([]))  # type: ignore[arg-type]
    monkeypatch.setattr(store, "get_project", lambda *args: {"readyForResearch": False})
    with pytest.raises(HTTPException, match="Confirm the journal"):
        store.start_job(PRINCIPAL, "project", "request-key")

    succeeded = HostedFoundationStore(ScriptedClient([[job_row("succeeded")]]))  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="cannot be cancelled"):
        succeeded.cancel_job(PRINCIPAL, str(job_row()["id"]))

    profile = HostedJournalProfileRepository(ScriptedClient([[{"version_id": "old", "version": 2}]]))  # type: ignore[arg-type]
    evidence = make_evidence("official-guide", "https://journals.aps.org/guide", "Guide", "guide")
    with pytest.raises(HTTPException, match="concurrently updated"):
        profile.publish(
            "0031-9007",
            [evidence],
            [{"claimClass": "verified fact", "sourceIds": [evidence.source_id], "locator": "page"}],
            [],
            1,
        )


def test_missing_hosted_profile_analysis_and_manuscript(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = HostedJournalProfileRepository(ScriptedClient([[]]))  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="Journal profile"):
        profile.get("missing")

    analysis = HostedAnalysisRepository(ScriptedClient([[]]))  # type: ignore[arg-type]
    with pytest.raises(HTTPException, match="Analysis not found"):
        analysis.get(PRINCIPAL, "missing")

    store = HostedFoundationStore(ScriptedClient([[]]))  # type: ignore[arg-type]
    monkeypatch.setattr(store, "_project_row", lambda *args: project_row())
    with pytest.raises(HTTPException, match="validated manuscript"):
        store.manuscript_record(PRINCIPAL, "project")
