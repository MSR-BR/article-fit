from __future__ import annotations

import hashlib
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient
from journal_matcher_api.foundation import FoundationStore, Principal

from tests.conftest import WORKSPACE_A, auth, synthetic_docx
from tests.integration.test_ingestion_flow import create_project, upload


def test_backup_restore_and_non_destructive_rollback_drill(
    client: TestClient, store: FoundationStore, tmp_path: Path
) -> None:
    project_id = create_project(client)
    upload(
        client,
        project_id,
        "manuscript",
        synthetic_docx(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    source_hashes = {
        path.relative_to(store.object_root): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in store.object_root.rglob("*")
        if path.is_file()
    }

    backup_root = tmp_path / "backup"
    backup_root.mkdir()
    with (
        closing(sqlite3.connect(store.database_path)) as source,
        closing(sqlite3.connect(backup_root / "metadata.sqlite3")) as target,
    ):
        source.backup(target)
    shutil.copytree(store.object_root, backup_root / "objects")

    restored = FoundationStore(backup_root / "metadata.sqlite3", backup_root / "objects")
    principal = Principal("invited-pilot-user", WORKSPACE_A)
    project = restored.get_project(principal, project_id)
    restored_hashes = {
        path.relative_to(restored.object_root): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in restored.object_root.rglob("*")
        if path.is_file()
    }
    assert project["id"] == project_id
    assert restored_hashes == source_hashes

    assert client.delete(f"/v1/projects/{project_id}", headers=auth()).status_code == 204
    assert not [path for path in store.object_root.rglob("*") if path.is_file()]
    assert restored.get_project(principal, project_id)["id"] == project_id
