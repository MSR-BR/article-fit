from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from journal_matcher_api.foundation import FoundationStore
from journal_matcher_api.main import app, get_store

WORKSPACE_A = "11111111-1111-4111-8111-111111111111"
WORKSPACE_B = "22222222-2222-4222-8222-222222222222"


@pytest.fixture
def store(tmp_path: Path) -> FoundationStore:
    return FoundationStore(tmp_path / "metadata.sqlite3", tmp_path / "objects")


@pytest.fixture
def client(store: FoundationStore) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth(workspace: str = WORKSPACE_A) -> dict[str, str]:
    return {"Authorization": "Bearer local-invite-token", "X-Workspace-Id": workspace}


def synthetic_pdf(label: str = "synthetic") -> bytes:
    from journal_matcher_api.manuscript_analysis import create_pdf

    prose = f"{label} methods results discussion evidence " * 30
    return create_pdf("Synthetic article", [prose])


def synthetic_docx() -> bytes:
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<w:document><w:body><w:p><w:r><w:t>"
            + ("Synthetic manuscript methods and results. " * 30)
            + "</w:t></w:r></w:p></w:body></w:document>",
        )
    return stream.getvalue()
