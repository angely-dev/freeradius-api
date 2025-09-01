import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the database connection to avoid connecting to a real database
with patch('src.database.get_db_connection'):
    from src.api import app

client = TestClient(app)


def test_user_creation_with_invalid_data():
    """Test user creation with invalid data returns proper error"""
    # Test user with no attributes
    invalid_user = {"username": "test-user"}
    response = client.post("/users", json=invalid_user)
    assert response.status_code == 422  # Validation error


def test_group_creation_with_invalid_data():
    """Test group creation with invalid data returns proper error"""
    # Test group with no attributes
    invalid_group = {"groupname": "test-group"}
    response = client.post("/groups", json=invalid_group)
    assert response.status_code == 422  # Validation error


def test_nas_creation_with_invalid_data():
    """Test NAS creation with invalid data returns proper error"""
    # Test NAS with no secret
    invalid_nas = {"nasname": "192.168.1.1"}
    response = client.post("/nas", json=invalid_nas)
    assert response.status_code == 422  # Validation error


def test_get_nonexistent_resources():
    """Test getting nonexistent resources returns 404"""
    response = client.get("/users/nonexistent-user")
    assert response.status_code == 404
    
    response = client.get("/groups/nonexistent-group")
    assert response.status_code == 404
    
    response = client.get("/nas/nonexistent-nas")
    assert response.status_code == 404


def test_patch_nonexistent_resources():
    """Test patching nonexistent resources returns 404"""
    patch_data = {"checks": [{"attribute": "Cleartext-Password", "op": ":=", "value": "new-pass"}]}
    
    response = client.patch("/users/nonexistent-user", json=patch_data)
    assert response.status_code == 404
    
    response = client.patch("/groups/nonexistent-group", json={"replies": []})
    assert response.status_code == 404
    
    response = client.patch("/nas/nonexistent-nas", json={"secret": "new-secret"})
    assert response.status_code == 404


def test_delete_nonexistent_resources():
    """Test deleting nonexistent resources returns 404"""
    response = client.delete("/users/nonexistent-user")
    assert response.status_code == 404
    
    response = client.delete("/groups/nonexistent-group")
    assert response.status_code == 404
    
    response = client.delete("/nas/nonexistent-nas")
    assert response.status_code == 404