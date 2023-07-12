"""The collections of the tests for the tools/database.py module."""
from pathlib import Path

from unittest.mock import patch, call
import pytest

import tools.database
from tools.database import Database


@patch('tools.database.Database.create_session')
@patch('tools.database.Database.__exit__')
def test_create_session_if_use_as_context_manager(
    mock_exit,
    mock_create_session,
):
    """Test that sessions were created when Database is used as a context manager.

    Args:
        mock_create_session: mock object for 'tools.protection.Protection.save_database_dump' method
        mock_exit: mock object for 'tools.database.Database.__exit__' method
    """
    with Database(Path('database.db'), 'password') as database:
        pass

    mock_create_session.assert_called_once()
    mock_exit.assert_called_once()


@patch('tools.models.Base.metadata.create_all')
@patch('tools.database.Path.exists', return_value=True)
def test_create_database_if_exists(mock_path, mock_base):
    """Test that 'create_database' raises a 'FileExistsError' when database file is already exists.

    Args:
        mock_path: mock object for 'tools.models.Base.metadata.create_all' method
        mock_base: mock object for 'tools.database.Path.exists' method
    """
    database = Database(Path('database.db'), 'password')

    with pytest.raises(FileExistsError) as error:
        database.create_database()

    assert error.type == FileExistsError
    mock_base.assert_not_called()
    mock_path.assert_called_once()


@patch('tools.models.Base.metadata.create_all')
@patch('tools.database.Path.exists', return_value=False)
def test_create_database_if_not_exists(mock_path, mock_base):
    """Test that the database file was created if the 'create_database' method was called
        and the database file don't exist.

    Args:
        mock_path: mock object for 'tools.database.Path.exists' method
        mock_base: mock object for 'tools.models.Base.metadata.create_all' method
    """
    database = Database(Path('database.db'), 'password')

    database.create_database()

    mock_base.assert_called_once()
    mock_path.assert_called_once()


@patch('tools.database.Session')
def test_create_session(mock_session):
    """Test the creation of a database session using the 'create_database' method of the 'Database' class

    Args:
        mock_session: mock object for the 'Session' class
    """
    database = Database(Path('db.db'), 'password')

    database.create_session()

    mock_session.assert_called_once()
    assert database.session == mock_session().__enter__()


@patch('tools.database.create_engine')
def test_dump_database(mock_create_engine):
    """Test the 'dump' method of the 'Database' class

    Args:
        mock_create_engine: mock object for 'tools.database.create_engine' method
    """
    expected_result = 'some data'
    mock_create_engine.return_value.raw_connection.return_value.iterdump.return_value = expected_result
    database = Database(Path('db.db'), 'password')

    result = database.dump()
    mock_create_engine.assert_called()

    assert result == b's\no\nm\ne\n \nd\na\nt\na\n'


@patch('tools.database.text')
@patch('tools.database.Protection.decrypt_file', return_value='script1')
@patch('tools.database.Session.execute')
def test_load_data_to_database(mock_session, mock_protection, mock_text):
    """Test the 'load' method of the 'Database' class to ensure data is loaded correctly.

    Args:
        mock_session: mock object for 'tools.database.Session.execute' method
        mock_protection: mock object for 'tools.database.Protection.decrypt_file' method
        mock_text: mock object for 'tools.database.text' method
    """
    database = Database(Path('db.db'), 'password')
    database.create_session()

    database.load()

    calls = [call(mock_text('script1'))]
    mock_session.assert_has_calls(calls)
    mock_protection.assert_called_once()
    assert mock_session.call_count == 1
