import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from journal_matcher_api.main import _trigger_cloud_run_worker, app


class FakeResponse:
    def __init__(self, payload: bytes = b"") -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_api_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"service": "api", "status": "ok", "version": "0.1.0"}


def test_worker_trigger_is_optional_and_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUD_RUN_WORKER_RUN_URL", raising=False)
    assert _trigger_cloud_run_worker() is None
    monkeypatch.setenv("CLOUD_RUN_WORKER_RUN_URL", "https://example.test/job:run")
    with pytest.raises(HTTPException, match="misconfigured"):
        _trigger_cloud_run_worker()


def test_worker_trigger_uses_metadata_token_without_logging_it(monkeypatch: pytest.MonkeyPatch) -> None:
    run_url = "https://run.googleapis.com/v2/projects/p/locations/r/jobs/w:run"
    monkeypatch.setenv("CLOUD_RUN_WORKER_RUN_URL", run_url)
    calls: list[object] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        calls.append(request)
        assert timeout in {5, 10}
        if len(calls) == 1:
            return FakeResponse(json.dumps({"access_token": "runtime-token"}).encode())
        assert request.full_url == run_url  # type: ignore[attr-defined]
        assert request.headers["Authorization"] == "Bearer runtime-token"  # type: ignore[attr-defined]
        return FakeResponse()

    monkeypatch.setattr("journal_matcher_api.main.urlopen", fake_urlopen)
    assert _trigger_cloud_run_worker() is None
    assert len(calls) == 2


def test_worker_trigger_fails_closed_without_metadata_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_RUN_WORKER_RUN_URL", "https://run.googleapis.com/v2/projects/p/locations/r/jobs/w:run")
    monkeypatch.setattr("journal_matcher_api.main.urlopen", lambda *args, **kwargs: FakeResponse(b"{}"))
    with pytest.raises(HTTPException, match="could not be started"):
        _trigger_cloud_run_worker()
