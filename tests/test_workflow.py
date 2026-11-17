def test_full_workflow_lifecycle(client):
    # 1. Creator logs in and submits draft
    creator_login = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@novatech.com", "password": "Password123!"},
    )
    creator_token = creator_login.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    submit_res = client.post(
        "/api/v1/content/submit",
        data={
            "title": "NovaBook Pro Q4 Launch Ad",
            "content_type": "text",
            "original_text": "Introducing NovaBook Pro! The world's number one laptop with 24 hours of battery life and a 5-year warranty. Guaranteed success for every user!",
        },
        headers=creator_headers,
    )
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    sub_id = sub_data["id"]
    assert sub_data["current_status"] == "draft"

    # 2. Run Compliance Audit
    audit_res = client.post(
        f"/api/v1/compliance/audit/{sub_id}", headers=creator_headers
    )
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total_violations"] >= 4
    assert audit_data["critical_count"] >= 2  # Battery + Warranty

    # 3. Creator submits for review
    status_res = client.post(
        f"/api/v1/workflow/{sub_id}/status",
        json={
            "new_status": "submitted",
            "comment": "Submitting first draft for compliance review.",
        },
        headers=creator_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["current_status"] == "submitted"

    # 4. Reviewer logs in
    reviewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@novatech.com", "password": "Password123!"},
    )
    reviewer_token = reviewer_login.json()["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    # Reviewer adds comment requesting changes
    comment_res = client.post(
        f"/api/v1/workflow/{sub_id}/comment",
        json={
            "comment": "Please align battery hours with the 12-hour spec and remove unverified superiority claims.",
            "status_transition": "submitted -> changes_requested",
        },
        headers=reviewer_headers,
    )
    assert comment_res.status_code == 200

    change_req_res = client.post(
        f"/api/v1/workflow/{sub_id}/status",
        json={"new_status": "changes_requested", "comment": "Specs need correction."},
        headers=reviewer_headers,
    )
    assert change_req_res.status_code == 200
    assert change_req_res.json()["current_status"] == "changes_requested"

    # 5. Creator saves revised content based on AI recommendation
    rev_res = client.post(
        f"/api/v1/workflow/{sub_id}/revision",
        json={
            "content": audit_data["suggested_revision"],
            "version_label": "User Edit",
            "changes_summary": "Applied approved specifications and tone corrections.",
        },
        headers=creator_headers,
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["revision_number"] == 2

    # 6. Re-audit submission with revised text
    re_audit = client.post(
        f"/api/v1/compliance/audit/{sub_id}", headers=creator_headers
    )
    assert re_audit.status_code == 200
    assert re_audit.json()["overall_score"] >= 90.0, (
        "Revised text should score high compliance"
    )

    # 7. Reviewer approves
    approve_res = client.post(
        f"/api/v1/workflow/{sub_id}/status",
        json={
            "new_status": "approved",
            "comment": "Approved for enterprise launch publication.",
        },
        headers=reviewer_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["current_status"] == "approved"
