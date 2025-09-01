import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the database connection to avoid connecting to a real database
with patch('src.database.get_db_connection'):
    from src.api import app

client = TestClient(app)


def test_pagination_endpoints_exist():
    """Test that pagination endpoints exist and return 200"""
    response = client.get("/nas")
    assert response.status_code == 200
    
    response = client.get("/users")
    assert response.status_code == 200
    
    response = client.get("/groups")
    assert response.status_code == 200