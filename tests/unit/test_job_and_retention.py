from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from journal_matcher_api.foundation import FoundationStore, Principal, new_id, utc_now

from tests.conftest import WORKSPACE_A


def test_cancel_queued_job_and_purge_expired_project(store: FoundationStore) -> None:
    principal = Principal("user", WORKSPACE_A)
    project = store.create_project(principal, "Synthetic Journal")
    job_id = new_id()
    with store.connect() as connection:
        connection.execute(
            """INSERT INTO jobs
               (id, project_id, workspace_id, idempotency_key, state, stage, progress,
                error_code, error_detail, retry_eligible, cancel_requested, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'queued', 'validation', 0, NULL, NULL, 0, 0, ?, ?)""",
            (job_id, project["id"], WORKSPACE_A, "queued-key", utc_now(), utc_now()),
        )
    cancelled = store.cancel_job(principal, job_id)
    assert cancelled["state"] == "cancelled"

    old_date = (datetime.now(UTC) - timedelta(days=31)).isoformat()
    with store.connect() as connection:
        connection.execute("UPDATE projects SET created_at = ? WHERE id = ?", (old_date, project["id"]))
    assert store.purge_expired() == 1
    with pytest.raises(HTTPException):
        store.get_project(principal, str(project["id"]))


def test_missing_job_is_workspace_safe(store: FoundationStore) -> None:
    with pytest.raises(HTTPException) as error:
        store.get_job(Principal("user", WORKSPACE_A), new_id())
    assert error.value.status_code == 404
