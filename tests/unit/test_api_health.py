from fastapi.testclient import TestClient
from journal_matcher_api.main import app


def test_api_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"service": "api", "status": "ok", "version": "0.1.0"}
