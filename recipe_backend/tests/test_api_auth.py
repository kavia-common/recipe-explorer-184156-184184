from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_register_and_login_and_me():
    # Register
    r = client.post("/auth/register", params={"email": "user1@example.com", "password": "secret123", "username": "u1"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == "user1@example.com"

    # Login
    r = client.post("/auth/login", json={"email": "user1@example.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token

    # Me
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["email"] == "user1@example.com"
