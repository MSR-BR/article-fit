from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from journal_matcher_api import research_starter
from journal_matcher_api.research_starter import ResearchStarterClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_research_starter_contract_and_secret_boundary(monkeypatch) -> None:
    captured_authorization = ""

    def open_ok(request, timeout):
        nonlocal captured_authorization
        captured_authorization = request.headers["Authorization"]
        assert timeout == 45.0
        return FakeResponse(
            {
                "ok": True,
                "apiVersion": "v1",
                "contractVersion": "2026-07-27.c84",
                "reportId": "report-1",
                "references": [{"title": "Paper"}],
                "topPapers": [{"title": "Paper", "doi": "10.1/test"}],
                "coverage": {"rankedPapers": 1},
                "warnings": ["partial"],
                "unknownAdditiveField": True,
            }
        )

    monkeypatch.setattr(research_starter, "urlopen", open_ok)
    result = ResearchStarterClient("https://researchstarter.vercel.app", "secret-key-with-safe-length").report(
        "Physical Review Letters"
    )
    assert captured_authorization == "Bearer secret-key-with-safe-length"
    assert result.report_id == "report-1"
    assert result.contract_version == "2026-07-27.c84"
    assert result.warnings == ["partial"]
    assert "secret-key" not in repr(result)


def test_research_starter_fails_closed_without_leaking_key(monkeypatch) -> None:
    def denied(request, timeout):
        raise HTTPError(request.full_url, 401, "denied", {}, None)

    monkeypatch.setattr(research_starter, "urlopen", denied)
    with pytest.raises(HTTPException) as error:
        ResearchStarterClient("https://researchstarter.vercel.app", "secret-key-with-safe-length").report("topic")
    assert error.value.status_code == 401
    assert "secret-key" not in str(error.value.detail)


def test_research_starter_validates_base_topic_and_limits() -> None:
    with pytest.raises(ValueError, match="public HTTPS"):
        ResearchStarterClient("http://localhost", "secret-key-with-safe-length")
    client = ResearchStarterClient("https://researchstarter.vercel.app", "secret-key-with-safe-length")
    with pytest.raises(HTTPException, match="1 to 180"):
        client.report("")
    with pytest.raises(HTTPException, match="outside"):
        client.report("topic", max_references=81)
