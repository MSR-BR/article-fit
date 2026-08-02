import json
from typing import Any

import pytest
from fastapi import HTTPException
from journal_matcher_worker.main import health_payload, hosted_store, main, process_batch, process_message


class FakeHostedStore:
    def __init__(self, *, attempts: int = 0, state: str = "queued") -> None:
        self.job = {
            "id": "job-1",
            "project_id": "project-1",
            "workspace_id": "11111111-1111-4111-8111-111111111111",
            "attempt_count": attempts,
            "state": state,
            "progress": 0,
        }
        self.updates: list[dict[str, object]] = []
        self.deleted: list[int] = []
        self.deleted_projects: list[str] = []
        self.messages: list[dict[str, Any]] = []

    def worker_job(self, job_id: str) -> dict[str, Any] | None:
        return self.job if job_id == "job-1" else None

    def update_worker_job(self, job_id: str, **payload: object) -> dict[str, Any]:
        assert job_id == "job-1"
        self.updates.append(payload)
        self.job.update(payload)
        if payload.get("increment_attempt"):
            self.job["attempt_count"] = int(self.job["attempt_count"]) + 1
        return dict(self.job)

    def delete_queue_message(self, message_id: int) -> None:
        self.deleted.append(message_id)

    def read_queue(self, batch_size: int, visibility_seconds: int) -> list[dict[str, Any]]:
        del batch_size, visibility_seconds
        messages, self.messages = self.messages, []
        return messages

    def purge_expired(self) -> int:
        return 2

    def delete_source_documents(self, principal: object, project_id: str) -> int:
        del principal
        self.deleted_projects.append(project_id)
        return 4


QUEUE_ROW = {
    "msg_id": 7,
    "message": {"job_id": "job-1", "workflow": {"idempotencyKey": "request-1"}},
}


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


def test_hosted_store_requires_server_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="requires SUPABASE"):
        hosted_store()
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    assert hosted_store().client is not None


def test_worker_processes_and_acknowledges_message(monkeypatch: pytest.MonkeyPatch) -> None:
    async def successful_workflow(*args: object, **kwargs: object) -> dict[str, object]:
        del args
        progress_callback = kwargs["progress_callback"]
        assert callable(progress_callback)
        progress_callback("ai-review", 78)
        progress_callback("artifact-generation", 98)
        return {"state": "succeeded"}

    monkeypatch.setattr("journal_matcher_worker.main.execute_project_workflow", successful_workflow)
    store = FakeHostedStore()
    assert process_message(store, QUEUE_ROW) is True  # type: ignore[arg-type]
    assert store.deleted == [7]
    assert any(update.get("stage") == "ai-review" for update in store.updates)
    assert any(update.get("progress") == 98 for update in store.updates)
    assert store.updates[-1]["state"] == "succeeded"


def test_worker_retries_then_terminally_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def failed_workflow(*args: object, **kwargs: object) -> dict[str, object]:
        del args
        progress_callback = kwargs["progress_callback"]
        assert callable(progress_callback)
        progress_callback("ai-review", 82)
        raise HTTPException(status_code=502, detail="provider failed")

    monkeypatch.setattr("journal_matcher_worker.main.execute_project_workflow", failed_workflow)
    retrying = FakeHostedStore(attempts=0)
    assert process_message(retrying, QUEUE_ROW) is False  # type: ignore[arg-type]
    assert retrying.deleted == []
    assert retrying.updates[-1]["state"] == "queued"
    assert retrying.updates[-1]["retry_eligible"] is True

    terminal = FakeHostedStore(attempts=2)
    assert process_message(terminal, QUEUE_ROW) is False  # type: ignore[arg-type]
    assert terminal.deleted == [7]
    assert terminal.deleted_projects == ["project-1"]
    assert terminal.updates[-1]["state"] == "failed"
    assert terminal.updates[-1]["stage"] == "ai-review"
    assert terminal.updates[-1]["progress"] == 82
    assert terminal.updates[-1]["error_detail"] == "provider failed"
    failure_log = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert failure_log["errorCode"] == "workflow-502"
    assert failure_log["detail"] == "provider failed"


def test_worker_honors_cancellation_during_workflow(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = FakeHostedStore()

    async def cancelled_workflow(*args: object, **kwargs: object) -> dict[str, object]:
        del args
        store.job["state"] = "cancelled"
        progress_callback = kwargs["progress_callback"]
        assert callable(progress_callback)
        progress_callback("journal-research", 40)
        return {"state": "succeeded"}

    monkeypatch.setattr("journal_matcher_worker.main.execute_project_workflow", cancelled_workflow)
    assert process_message(store, QUEUE_ROW) is True  # type: ignore[arg-type]
    assert store.deleted == [7]
    assert not any(update.get("state") == "succeeded" for update in store.updates)
    assert json.loads(capsys.readouterr().out)["event"] == "workflow.cancelled"


def test_worker_discards_poison_and_terminal_messages() -> None:
    with pytest.raises(RuntimeError, match="invalid message envelope"):
        process_message(FakeHostedStore(), {"msg_id": "bad", "message": {}})  # type: ignore[arg-type]
    poison = FakeHostedStore()
    assert process_message(poison, {"msg_id": 3, "message": {}}) is False  # type: ignore[arg-type]
    assert poison.deleted == [3]
    terminal = FakeHostedStore(state="cancelled")
    assert process_message(terminal, QUEUE_ROW) is True  # type: ignore[arg-type]
    assert terminal.deleted == [7]
    assert terminal.deleted_projects == ["project-1"]


def test_process_batch_and_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    store = FakeHostedStore()
    monkeypatch.setattr("journal_matcher_worker.main.hosted_store", lambda: store)
    assert process_batch(1) == 0
    assert json.loads(capsys.readouterr().out) == {"failures": 0, "processed": 0}
    store.messages = [QUEUE_ROW]
    monkeypatch.setattr("journal_matcher_worker.main.process_message", lambda *args: True)
    assert process_batch(1) == 0
    assert json.loads(capsys.readouterr().out) == {"failures": 0, "processed": 1}
    assert main(["--process-batch", "--batch-size", "1"]) == 0


def test_hosted_retention_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("JOURNAL_MATCHER_PERSISTENCE", "supabase")
    monkeypatch.setattr("journal_matcher_worker.main.hosted_store", FakeHostedStore)
    assert main(["--purge-expired"]) == 0
    assert json.loads(capsys.readouterr().out) == {"purgedProjects": 2}
