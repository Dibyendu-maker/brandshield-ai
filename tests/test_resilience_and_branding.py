from unittest.mock import MagicMock
from pathlib import Path
import requests

from frontend.api_client import APIClient
from backend.database.models import ContentSubmission, Organization, User
from backend.core.security import get_password_hash, create_access_token


def _get_creator_auth(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@novatech.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoints(client):
    """Verifies that both root /health and /api/v1/health return healthy status."""
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json() == {"status": "healthy"}

    res_api = client.get("/api/v1/health")
    assert res_api.status_code == 200
    assert res_api.json() == {"status": "healthy"}


def test_api_client_health_check_online(monkeypatch):
    """Verifies APIClient.check_health returns healthy=True when backend responds."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "healthy"}

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

    api_client = APIClient("http://127.0.0.1:8000/api/v1")
    health = api_client.check_health()
    assert health["healthy"] is True
    assert health["details"] == {"status": "healthy"}


def test_api_client_health_check_offline(monkeypatch):
    """Verifies APIClient.check_health returns healthy=False gracefully when backend is unreachable."""
    def mock_get_fail(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection refused: 127.0.0.1:8000")

    monkeypatch.setattr(requests, "get", mock_get_fail)

    api_client = APIClient("http://127.0.0.1:8000/api/v1")
    health = api_client.check_health()
    assert health["healthy"] is False
    assert health["details"] is None


def test_submission_restoration_and_authorization(client, db_session):
    """Verifies query param submission ID validation: valid IDs succeed, non-existent,
    malformed, and cross-organization unauthorized IDs are safely rejected.
    """
    headers = _get_creator_auth(client)

    # 1. Create submission under NovaTech (Org 1)
    res = client.post(
        "/api/v1/content/submit",
        data={"title": "Resilience Test Doc", "original_text": "Sample valid content."},
        headers=headers,
    )
    assert res.status_code == 200
    valid_sub_id = res.json()["id"]

    # Valid authorized fetch succeeds
    get_res = client.get(f"/api/v1/content/{valid_sub_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == valid_sub_id

    # 2. Non-existent ID returns 404
    missing_res = client.get("/api/v1/content/999999", headers=headers)
    assert missing_res.status_code == 404

    # 3. Create a separate tenant organization and submission
    other_org = Organization(name="Other Corp", slug="othercorp")
    db_session.add(other_org)
    db_session.commit()
    db_session.refresh(other_org)

    other_user = User(
        organization_id=other_org.id,
        email="user@othercorp.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Other User",
        role="creator",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    other_submission = ContentSubmission(
        organization_id=other_org.id,
        creator_id=other_user.id,
        title="Confidential Other Corp Doc",
        content_type="text",
        original_text="Secret external content",
        current_status="draft",
        compliance_score=100.0,
    )
    db_session.add(other_submission)
    db_session.commit()
    db_session.refresh(other_submission)
    foreign_sub_id = other_submission.id

    # 4. Attempting to access foreign organization submission with NovaTech token returns 404 (isolated!)
    cross_org_res = client.get(f"/api/v1/content/{foreign_sub_id}", headers=headers)
    assert cross_org_res.status_code == 404, "Cross-tenant submission must return 404 Not Found"


def test_branding_has_no_stale_competition_references():
    """Verifies that all stale competition references have been eliminated in favor of CodeZen India 2026 Round 2."""
    app_text = Path("frontend/app.py").read_text(encoding="utf-8")
    readme_text = Path("README.md").read_text(encoding="utf-8")

    assert "Inkloom" not in app_text, "Found stale Inkloom reference in frontend/app.py"
    assert "Inkloom" not in readme_text, "Found stale Inkloom reference in README.md"

    assert "CodeZen India 2026 Round 2" in app_text, "Expected 'CodeZen India 2026 Round 2' in frontend/app.py"
    assert "CodeZen India 2026 Round 2" in readme_text, "Expected 'CodeZen India 2026 Round 2' in README.md"
