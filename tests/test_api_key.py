import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

# Test API key functionality
def test_api_key_disabled_by_default():
    """Test that API key authentication is disabled by default"""
    # Save original environment
    original_api_key_enabled = os.environ.get("API_KEY_ENABLED")
    
    # Remove API_KEY_ENABLED from environment if it exists
    if "API_KEY_ENABLED" in os.environ:
        del os.environ["API_KEY_ENABLED"]
    
    try:
        with patch("src.database.get_db_connection"):
            from src.config import AppSettings
            settings = AppSettings()
            assert settings.api_key_enabled == False
    finally:
        # Restore original environment
        if original_api_key_enabled is not None:
            os.environ["API_KEY_ENABLED"] = original_api_key_enabled


def test_api_key_can_be_enabled():
    """Test that API key authentication can be enabled"""
    # Save original environment
    original_api_key_enabled = os.environ.get("API_KEY_ENABLED")
    original_api_key = os.environ.get("API_KEY")
    original_api_key_header = os.environ.get("API_KEY_HEADER")
    
    try:
        os.environ["API_KEY_ENABLED"] = "true"
        os.environ["API_KEY"] = "test-key-123"
        os.environ["API_KEY_HEADER"] = "X-Test-Key"
        
        with patch("src.database.get_db_connection"):
            from src.config import AppSettings
            settings = AppSettings()
            assert settings.api_key_enabled == True
            assert settings.api_key == "test-key-123"
            assert settings.api_key_header == "X-Test-Key"
    finally:
        # Restore original environment
        if original_api_key_enabled is not None:
            os.environ["API_KEY_ENABLED"] = original_api_key_enabled
        else:
            os.environ.pop("API_KEY_ENABLED", None)
            
        if original_api_key is not None:
            os.environ["API_KEY"] = original_api_key
        else:
            os.environ.pop("API_KEY", None)
            
        if original_api_key_header is not None:
            os.environ["API_KEY_HEADER"] = original_api_key_header
        else:
            os.environ.pop("API_KEY_HEADER", None)
