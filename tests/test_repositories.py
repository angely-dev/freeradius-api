import pytest
from unittest.mock import Mock, patch, MagicMock

from src.pyfreeradius import (
    UserRepository,
    GroupRepository,
    NasRepository,
    User,
    Group,
    Nas,
    AttributeOpValue,
    UserGroup
)
from src.config import RadTables


class TestUserRepository:
    """Test UserRepository functionality"""

    @pytest.fixture
    def mock_db_connection(self):
        return Mock()

    @pytest.fixture
    def mock_db_tables(self):
        return RadTables()

    @pytest.fixture
    def user_repo(self, mock_db_connection, mock_db_tables):
        return UserRepository(mock_db_connection, mock_db_tables)

    def test_exists_returns_true_when_user_found(self, user_repo):
        """Test that exists returns True when user is found"""
        with patch.object(user_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return results with count > 0
            mock_cursor.fetchall.return_value = [(1,), (0,), (0,)]  # Count > 0 in first table

            result = user_repo.exists("test-user")
            assert result is True

    def test_exists_returns_false_when_user_not_found(self, user_repo):
        """Test that exists returns False when user is not found"""
        with patch.object(user_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return results with count = 0
            mock_cursor.fetchall.return_value = [(0,), (0,), (0,)]  # Count = 0 in all tables

            result = user_repo.exists("test-user")
            assert result is False

    def test_exists_handles_empty_results(self, user_repo):
        """Test that exists handles empty results gracefully"""
        with patch.object(user_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return empty results
            mock_cursor.fetchall.return_value = []  # Empty results

            result = user_repo.exists("test-user")
            assert result is False


class TestGroupRepository:
    """Test GroupRepository functionality"""

    @pytest.fixture
    def mock_db_connection(self):
        return Mock()

    @pytest.fixture
    def mock_db_tables(self):
        return RadTables()

    @pytest.fixture
    def group_repo(self, mock_db_connection, mock_db_tables):
        return GroupRepository(mock_db_connection, mock_db_tables)

    def test_exists_returns_true_when_group_found(self, group_repo):
        """Test that exists returns True when group is found"""
        with patch.object(group_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return results with count > 0
            mock_cursor.fetchall.return_value = [(1,), (0,)]  # Count > 0 in first table

            result = group_repo.exists("test-group")
            assert result is True

    def test_exists_returns_false_when_group_not_found(self, group_repo):
        """Test that exists returns False when group is not found"""
        with patch.object(group_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return results with count = 0
            mock_cursor.fetchall.return_value = [(0,), (0,)]  # Count = 0 in all tables

            result = group_repo.exists("test-group")
            assert result is False

    def test_exists_handles_empty_results(self, group_repo):
        """Test that exists handles empty results gracefully"""
        with patch.object(group_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchall to return empty results
            mock_cursor.fetchall.return_value = []  # Empty results

            result = group_repo.exists("test-group")
            assert result is False


class TestNasRepository:
    """Test NasRepository functionality"""

    @pytest.fixture
    def mock_db_connection(self):
        return Mock()

    @pytest.fixture
    def mock_db_tables(self):
        return RadTables()

    @pytest.fixture
    def nas_repo(self, mock_db_connection, mock_db_tables):
        return NasRepository(mock_db_connection, mock_db_tables)

    def test_exists_returns_true_when_nas_found(self, nas_repo):
        """Test that exists returns True when NAS is found"""
        with patch.object(nas_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchone to return result with count > 0
            mock_cursor.fetchone.return_value = (1,)  # Count > 0

            result = nas_repo.exists("192.168.1.1")
            assert result is True

    def test_exists_returns_false_when_nas_not_found(self, nas_repo):
        """Test that exists returns False when NAS is not found"""
        with patch.object(nas_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchone to return result with count = 0
            mock_cursor.fetchone.return_value = (0,)  # Count = 0

            result = nas_repo.exists("192.168.1.1")
            assert result is False

    def test_exists_handles_none_result(self, nas_repo):
        """Test that exists handles None result gracefully"""
        with patch.object(nas_repo, "_db_cursor") as mock_cursor_context:
            mock_cursor = Mock()
            mock_cursor_context.return_value.__enter__.return_value = mock_cursor
            # Mock fetchone to return None
            mock_cursor.fetchone.return_value = None

            result = nas_repo.exists("192.168.1.1")
            assert result is False
