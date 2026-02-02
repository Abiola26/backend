
import pytest

def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={"username": "testuser", "password": "testpassword", "email": "test@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login(client):
    # First signup
    client.post(
        "/auth/signup",
        json={"username": "testuser", "password": "testpassword", "email": "test@example.com"}
    )
    
    # Then login
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/token",
        data={"username": "wronguser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
