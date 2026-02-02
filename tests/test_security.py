
import pytest


def test_unauthorized_access(client):
    # Try accessing protected route without token
    response = client.get("/analytics/summary")
    assert response.status_code == 401

def test_admin_only_route_as_user(client):
    # Create a regular user
    client.post("/auth/signup", json={"username": "normaluser", "password": "password", "role": "user"})
    login_res = client.post("/auth/token", data={"username": "normaluser", "password": "password"})
    data = login_res.json()
    if "access_token" not in data:
        pytest.fail(f"Login failed: {data}")
    token = data["access_token"]
    
    # Try accessing admin only route (e.g., list all users)
    response = client.get("/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
