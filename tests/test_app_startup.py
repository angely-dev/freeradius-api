import pytest
from unittest.mock import patch

# Test that the application can be imported without database connectivity
def test_app_import_without_database():
    """Test that the app can be imported without connecting to a database"""
    with patch('src.database.get_db_connection'):
        from src.api import app
        assert app is not None