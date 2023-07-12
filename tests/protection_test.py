"""The collections of the tests for the 'tools.protection.py' module"""
from pathlib import Path
from unittest.mock import patch, MagicMock

from cryptography.fernet import Fernet
from pytest import MonkeyPatch, fixture
import pytest

from tools.protection import Protection


class GzipOpenMock:
    """Mock 'gzip.open' method."""
    def __init__(self, *_):
        pass

    @staticmethod
    def read():
        """Mock the 'read' method of the 'gzip' object."""
        return 'some data, 123'

    @staticmethod
    def write(*_):
        """Mock the 'write' method of the 'gzip' object."""

    @staticmethod
    def close():
        """Mock the 'close' method of the 'gzip' object."""


@pytest.fixture(name='protection')
def fixture_protection(monkeypatch: MonkeyPatch):
    """Fixture for creating an instance of the Protection class.
        This fixture patches the 'tools.protection.gzip.open' function with a mock object.

    Args:
        monkeypatch (MonkeyPatch): a pytest fixture that provides the ability to modify
            the attributes or functions at runtime

    Returns:
        protection: a Protection object configured with the specified password and database path
    """
    monkeypatch.setattr('tools.protection.gzip.open', GzipOpenMock)
    protection = Protection('password', Path('database_path/database.db'))

    return protection


def test_key_create(protection: Protection):
    """Test case for the 'key_creation' method of the Protection class.

    Args:
        protection (Protection): an instance of the Protection class

    """
    key = protection.key_creation
    with patch('tools.protection.Fernet') as mock_fernet:
        key()

    mock_fernet.assert_called_once()
    assert isinstance(key(), Fernet)


@patch('tools.protection.Fernet.encrypt', return_value=b'expected value')
def test_encrypt_data(mock_encrypt: MagicMock, protection: Protection):
    """Test case for the 'encrypt_data' method of the Protection class.

    Args:
        mock_encrypt (MagicMock): the patched 'encrypt' method of the Fernet class
        protection (Protection): an instance of the Protection class
    """
    encrypted_data = protection.encrypt(b'some data')

    assert encrypted_data == b'expected value'
    mock_encrypt.assert_called_once_with(b'some data')


@patch('tools.protection.Fernet.decrypt', return_value=b'expected value')
def test_decrypt_data(mock_decrypt: MagicMock, protection: Protection):
    """Test case for the 'decrypt_data' method of the Protection class.

    Args:
        mock_decrypt (MagicMock): the patched 'decrypt' method of the Fernet class
        protection (Protection): an instance of the Protection class
    """
    encrypted_data = protection.decrypt('some data')

    assert encrypted_data == b'expected value'
    mock_decrypt.assert_called_once_with('some data')


@patch('tools.protection.Protection.decrypt', return_value=b'expected decrypted data')
def test_decrypt_file(mock_decrypt: MagicMock, protection: Protection):
    """Test case for the 'decrypt_file' method of the Protection class.

    Args:
        mock_decrypt (MagicMock): the patched 'decrypt' method of the Protection class
        protection (Protection): an instance of the Protection class
    """
    decrypted_file_data = protection.decrypt_file()

    assert decrypted_file_data == 'expected decrypted data'
    mock_decrypt.assert_called_once_with('some data, 123')


@patch.object(GzipOpenMock, 'write')
@patch('tools.protection.Protection.encrypt', return_value=b'expected encrypted data')
def test_save_database_dump(mock_encrypt: MagicMock, mock_gzip: MagicMock, protection: Protection):
    """Test case for the 'save_database_dump' method of the Protection class.

    Args:
        mock_encrypt (MagicMock): the patched 'encrypt' method of the Protection class
        mock_gzip (MagicMock): the patched 'open' method of the gzip object
        protection (Protection): an instance of the Protection class
    """
    protection.save_database_dump(b'dumped database')

    mock_gzip.assert_called_once_with(b'expected encrypted data')
    mock_encrypt.assert_called_once_with(b'dumped database')
