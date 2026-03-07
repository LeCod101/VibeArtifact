from api_app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_liveness():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
