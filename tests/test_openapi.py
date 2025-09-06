from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_openapi_loads():
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    assert "openapi" in r.json()

def test_docs_served():
    r = client.get("/api/docs")
    assert r.status_code == 200
