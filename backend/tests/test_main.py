from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# checks that FastAPI backend responds correctly
def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Elevate Solicitation Finder API",
        "status": "running",
    }


# checks that endpoint returns expected health status and using local development
# configuration
def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["environment"] == "development"
