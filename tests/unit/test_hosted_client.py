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
from journal_matcher_api.main import authenticate


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


def test_verify_user_uses_publishable_key_and_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["headers"] = dict(request.headers)  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return FakeResponse(json.dumps({"id": "11111111-1111-4111-8111-111111111111"}).encode())

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", fake_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret", "publishable-key"))
    assert client.verify_user("user-token")["id"] == "11111111-1111-4111-8111-111111111111"
    assert captured["url"] == "https://project.supabase.co/auth/v1/user"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Apikey"] == "publishable-key"
    assert headers["Authorization"] == "Bearer user-token"
    assert "server-secret" not in str(headers)


def test_verify_user_requires_hosted_auth_config_and_valid_session(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    with pytest.raises(HTTPException) as missing:
        client.verify_user("token")
    assert missing.value.status_code == 503

    def unauthorized(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        raise HTTPError("https://project.supabase.co/auth/v1/user", 401, "expired", {}, None)

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", unauthorized)
    configured = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret", "publishable-key"))
    with pytest.raises(HTTPException) as invalid:
        configured.verify_user("expired-token")
    assert invalid.value.status_code == 401


def test_verify_user_rejects_invalid_auth_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def invalid_json(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        return FakeResponse(b"not-json")

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", invalid_json)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret", "publishable-key"))
    with pytest.raises(HTTPException) as invalid:
        client.verify_user("user-token")
    assert invalid.value.status_code == 502


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


def test_storage_missing_object_is_normalized_and_delete_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        raise HTTPError(request.full_url, 400, "not found", {}, None)  # type: ignore[attr-defined]

    monkeypatch.setattr("journal_matcher_api.hosted.urlopen", missing_urlopen)
    client = SupabaseHttpClient(SupabaseSettings("https://project.supabase.co", "server-secret"))
    with pytest.raises(HTTPException) as caught:
        client.download("manuscripts", "workspace/missing.pdf")
    assert caught.value.status_code == 404
    client.delete_objects("manuscripts", ["workspace/missing.pdf"])


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


class AuthStubClient(StubClient):
    def __init__(self, user: dict[str, object], member: bool) -> None:
        super().__init__([[{"workspace_id": "11111111-1111-4111-8111-111111111111"}] if member else []])
        self.user = user

    def verify_user(self, access_token: str) -> dict[str, object]:
        assert access_token == "user-token"
        return self.user


def test_hosted_authentication_requires_named_workspace_member() -> None:
    user_id = "33333333-3333-4333-8333-333333333333"
    store = HostedFoundationStore(AuthStubClient({"id": user_id, "is_anonymous": False}, True))  # type: ignore[arg-type]
    principal = authenticate(
        store,
        "Bearer user-token",
        "11111111-1111-4111-8111-111111111111",
    )
    assert principal == Principal(user_id, "11111111-1111-4111-8111-111111111111")

    anonymous = HostedFoundationStore(AuthStubClient({"id": user_id, "is_anonymous": True}, True))  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as anonymous_error:
        authenticate(anonymous, "Bearer user-token", "11111111-1111-4111-8111-111111111111")
    assert anonymous_error.value.status_code == 401

    nonmember = HostedFoundationStore(AuthStubClient({"id": user_id, "is_anonymous": False}, False))  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as membership_error:
        authenticate(nonmember, "Bearer user-token", "11111111-1111-4111-8111-111111111111")
    assert membership_error.value.status_code == 403


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
