"""Unit tests for API service."""
import sys
sys.path.insert(0, '../api-service')

import pytest
from fastapi.testclient import TestClient
from main import app
from auth import AuthManager


client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/vehicles")
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    """Test accessing protected endpoint with valid token."""
    # First, login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/vehicles", headers=headers)
    
    # Should not return 401
    assert response.status_code != 401


def test_jwt_token_creation():
    """Test JWT token creation."""
    token = AuthManager.create_access_token({"sub": "testuser"})
    assert token is not None
    
    # Verify token
    token_data = AuthManager.verify_token(token)
    assert token_data is not None
    assert token_data.username == "testuser"


def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = AuthManager.hash_password(password)
    
    assert password != hashed
    assert AuthManager.verify_password(password, hashed)
    assert not AuthManager.verify_password("wrongpassword", hashed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
