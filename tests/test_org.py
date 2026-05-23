from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_org_registration_flow():
    payload = {
        "email": "owner@company.com",
        "company_name": "Acme Widgets Inc"
    }
    # Register triggers magic link send
    res = client.post("/api/org/register", json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
