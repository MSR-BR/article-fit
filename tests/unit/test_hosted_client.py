from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from journal_matcher_api.foundation import Principal
from journal_matcher_api.hosted import (
    HostedFoundationStore,
    HostedJournalProfileRepository,
    SupabaseHttpClient,
    SupabaseSettings,
    require_rows,
)


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_settings_require_https_and_privileged_key() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        SupabaseSettings("http://example.test", "secret")
    with pytest.raises(ValueError, match="SERVICE_ROLE"):
        SupabaseSettings("https://example.test", "")


def test_table_request_keeps_service_key_in_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["headers"] = dict(request.headers)  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return FakeResponse(json.dumps([{"id": "project-1"}]).encode())

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", fake_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    rows = client.table("projects", query={"select": "id", "workspace_id": "eq.workspace-1"})

    assert require_rows(rows) == [{"id": "project-1"}]
    assert "server-secret" not in str(captured["url"])
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer server-secret"
    assert headers["Apikey"] == "server-secret"


def test_upstream_error_does_not_echo_sensitive_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_urlopen(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        raise HTTPError("https://project.supabase.co", 500, "secret manuscript text", {}, None)

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", failing_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    with pytest.raises(HTTPException) as caught:
        client.table("projects")
    assert caught.value.status_code == 502
    assert "secret manuscript text" not in str(caught.value.detail)


def test_queue_rpc_selects_the_managed_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        captured.update(dict(request.headers))  # type: ignore[attr-defined]
        return FakeResponse(b"[]")

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", fake_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    client.rpc("read", {"queue_name": "analysis_jobs", "sleep_seconds": 300, "n": 1}, schema="pgmq_public")

    assert captured["Accept-profile"] == "pgmq_public"
    assert captured["Content-profile"] == "pgmq_public"


def test_private_object_deletion_uses_storage_object_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple[str, str]] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        captured.append((request.get_method(), request.full_url))  # type: ignore[attr-defined]
        return FakeResponse(b"")

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", fake_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    client.delete_objects("manuscripts", ["workspace/project/one.pdf", "workspace/project/two.pdf"])

    assert captured == [
        ("DELETE", "https://project.supabase.co/storage/v1/object/manuscripts/workspace/project/one.pdf"),
        ("DELETE", "https://project.supabase.co/storage/v1/object/manuscripts/workspace/project/two.pdf"),
    ]


def test_require_rows_rejects_invalid_shape() -> None:
    with pytest.raises(HTTPException, match="invalid row set"):
        require_rows({"id": "not-a-list"})


class StubClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def table(self, name: str, *, method: str = "GET", **kwargs: object) -> object:
        del kwargs
        self.calls.append((name, method))
        return self.responses.pop(0)


def test_hosted_project_payload_is_workspace_scoped() -> None:
    client = StubClient(
        [
            [
                {
                    "id": "project-1",
                    "journal_candidate": "Physical Review Letters",
                    "journal_title": None,
                    "journal_issn": None,
                    "journal_domain": None,
                    "journal_confirmed_at": None,
                    "created_at": "2026-08-01T00:00:00+00:00",
                }
            ],
            [],
        ]
    )
    store = HostedFoundationStore(client)  # type: ignore[arg-type]
    result = store.get_project(Principal("user-1", "11111111-1111-4111-8111-111111111111"), "project-1")

    assert result["journalCandidate"] == "Physical Review Letters"
    assert result["readyForResearch"] is False
    assert client.calls == [("projects", "GET"), ("documents", "GET")]


def test_hosted_profile_get_preserves_json_values() -> None:
    client = StubClient(
        [
            [
                {
                    "id": "profile-1",
                    "journal_issn": "0031-9007",
                    "version": 1,
                    "status": "published",
                    "claims_json": [{"key": "scope"}],
                    "evidence_json": [{"source_id": "official"}],
                    "limitations_json": [],
                    "created_at": "2026-08-01T00:00:00+00:00",
                    "supersedes_id": None,
                }
            ]
        ]
    )
    repository = HostedJournalProfileRepository(client)  # type: ignore[arg-type]
    profile = repository.get("profile-1")

    assert profile["journalIssn"] == "0031-9007"
    assert profile["claims"] == [{"key": "scope"}]
