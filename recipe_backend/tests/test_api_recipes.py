from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def auth_token(email="chef@example.com", password="cook12345"):
    client.post("/auth/register", params={"email": email, "password": password, "username": "chef"})
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_create_list_search_and_rate():
    token = auth_token()

    # Create recipes
    body = {
        "title": "Pasta Primavera",
        "description": "Fresh veggies pasta",
        "ingredients": ["pasta", "tomatoes", "peas"],
        "steps": ["boil pasta", "mix veggies"],
        "tags": ["italian", "vegetarian"],
        "metadata": {"cuisine": "Italian", "difficulty": "easy", "time": 25},
    }
    r = client.post("/recipes", json=body, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    created = r.json()
    recipe_id = created["id"]

    # List search
    r = client.get("/recipes", params={"search": "pasta", "sort": "newest"})
    assert r.status_code == 200, r.text
    items = r.json()
    assert any(it["id"] == recipe_id for it in items)

    # Rate
    r = client.post(f"/recipes/{recipe_id}/rate", json={"rating": 5}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    rated = r.json()
    assert rated["avg_rating"] >= 5.0 - 1e-6
