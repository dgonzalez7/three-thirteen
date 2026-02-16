from fastapi.testclient import TestClient
from app.main import app, DETECTIVES
client = TestClient(app)
def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200
def test_home_contains_detective_name():
    response = client.get("/")
    assert any(name in response.text for name in DETECTIVES)
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

