import pytest
from src.database import get_db_connection


def test_get_db_connection_unsupported():
    """Test unsupported database type raises ValueError"""
    with pytest.raises(ValueError, match="Unsupported database type"):
        get_db_connection("unsupported", "localhost", "user", "pass", "db")
