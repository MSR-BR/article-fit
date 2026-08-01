from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from journal_matcher_api.hosted import SupabaseHttpClient, SupabaseSettings, require_rows


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


def test_require_rows_rejects_invalid_shape() -> None:
    with pytest.raises(HTTPException, match="invalid row set"):
        require_rows({"id": "not-a-list"})
