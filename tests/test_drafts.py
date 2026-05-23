from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_save_and_resume_draft():
    # Save draft
    payload = {
        "email": "org-test@company.com",
        "company_name": "Test Company Ltd",
        "form_state": {"q5": "Yes", "q6": "No"},
        "current_step": 2
    }
    response = client.post("/api/drafts/save", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "draft_id" in data
    assert "resume_url" in data
    
    # Resume draft
    token = data["resume_url"].split("token=")[1]
    res_response = client.get(f"/api/drafts/resume?token={token}")
    assert res_response.status_code == 200
    res_data = res_response.json()
    assert res_data["email"] == "org-test@company.com"
    assert res_data["company_name"] == "Test Company Ltd"
    assert res_data["form_state"]["q5"] == "Yes"
