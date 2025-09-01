import pytest
from unittest.mock import patch, Mock

from src.database import get_db_connection


@patch('src.database.mysql.connector.connect')
def test_get_db_connection_mysql(mock_connect):
    """Test MySQL database connection"""
    mock_connection = Mock()
    mock_connect.return_value = mock_connection
    
    connection = get_db_connection('mysql', 'localhost', 'user', 'pass', 'db')
    
    mock_connect.assert_called_once_with(user='user', password='pass', host='localhost', database='db')
    assert connection == mock_connection


@patch('src.database.psycopg2.connect')
def test_get_db_connection_postgres(mock_connect):
    """Test PostgreSQL database connection"""
    mock_connection = Mock()
    mock_connect.return_value = mock_connection
    
    connection = get_db_connection('postgres', 'localhost', 'user', 'pass', 'db')
    
    mock_connect.assert_called_once_with(user='user', password='pass', host='localhost', database='db')
    assert connection == mock_connection


@patch('src.database.pymssql.connect')
def test_get_db_connection_mssql(mock_connect):
    """Test MSSQL database connection"""
    mock_connection = Mock()
    mock_connect.return_value = mock_connection
    
    connection = get_db_connection('mssql', 'localhost', 'user', 'pass', 'db')
    
    mock_connect.assert_called_once_with(user='user', password='pass', server='localhost', database='db')
    assert connection == mock_connection


@patch('src.database.sqlite3.connect')
def test_get_db_connection_sqlite(mock_connect):
    """Test SQLite database connection"""
    mock_connection = Mock()
    mock_connect.return_value = mock_connection
    
    connection = get_db_connection('sqlite', '', '', '', 'db.sqlite')
    
    mock_connect.assert_called_once_with('db.sqlite')
    assert connection == mock_connection


def test_get_db_connection_unsupported():
    """Test unsupported database type raises ValueError"""
    with pytest.raises(ValueError, match='Unsupported database type'):
        get_db_connection('unsupported', 'localhost', 'user', 'pass', 'db')