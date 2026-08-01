import json

import pytest
from journal_matcher_worker.main import health_payload, main


def test_worker_health_payload() -> None:
    assert health_payload() == {"service": "worker", "status": "ok", "version": "0.1.0"}


def test_worker_health_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--health-check"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == health_payload()


def test_worker_idle_shell(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "ingestion worker is ready" in captured.out
