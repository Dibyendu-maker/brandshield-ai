def test_login_success(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@novatech.com", "password": "Password123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "creator@novatech.com"
    assert data["user"]["role"] == "creator"


def test_login_invalid_password(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@novatech.com", "password": "WrongPassword!"},
    )
    assert res.status_code == 401


def test_user_registration(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@novatech.com",
            "password": "SecurePassword123!",
            "full_name": "New Tester",
            "role": "creator",
            "organization_slug": "novatech",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "newuser@novatech.com"


def test_me_endpoint_with_auth(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@novatech.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@novatech.com"
    assert me_res.json()["role"] == "admin"
