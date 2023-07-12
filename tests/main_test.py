"The collections of the tests for the 'main.py' module."
from datetime import date
from json import load
from unittest.mock import patch, MagicMock
from pathlib import Path
from requests import Session

import pytest
from pytest import MonkeyPatch

from tools.arbiko import Arbiko
from tools.database import Database
from tools.exceptions import DatabaseError
from tools.models import Order, OrderProduct, Product
from main import update_data, refresh_data


class ArbikoMock:
    """Mock Arbiko class.

    Methods:
        get_order_history (*_): mock the 'get_order_history' method of the Arbiko class
    """
    def __init__(self, *_):
        """Constructor"""

    @staticmethod
    def get_order_history(*_):
        """Mock the 'get_order_history' method of the Arbiko class.

        Returns:
            (dict): with the expected response
        """
        with open('tests/responses/expected_result_get_order_history.json') as file:
            expected_result = load(file)

        return expected_result


@pytest.fixture(autouse=True)
def no_requests(monkeypatch: MonkeyPatch):
    """Fixture for patching the 'request' method of the Session class
        to mock HTTP requests.

    Args:
        monkeypatch: the pytest monkeypatch fixture object
    """
    monkeypatch.delattr(Session, 'request')


@pytest.fixture(name='database')
@patch('tools.database.Protection.save_database_dump')
def database_connection(mock_protection: MagicMock) -> Database:
    """Fixture for creating an instance of the Database class.

    Args:
        mock_protection (MagicMock): the patched 'save_database_dump' method of the Protection class

    Returns:
        (Database): database session
    """
    with Database(Path('database_path.db'), 'password') as database:
        database.create_database()
        return database


@pytest.mark.parametrize(
    'start_date, end_date', (
        (None, None),
        (None, '2022-01-12'),
        ('2022-01-12', None),
        ('2021-01-12', '2022-01-12'),
        ('2022-01-12', '2022-01-12'),
    ),
)
@patch('tools.arbiko.Arbiko.login', return_value=True)
def test_update_data(
        mock_arbiko_login: MagicMock,
        start_date: str,
        end_date: str,
        monkeypatch: MonkeyPatch,
        database: Database
):
    """Test 'update_data' method of the 'main.py' module.

    Args:
        mock_arbiko_login (MagicMock): the patched 'login' method of the 'Arbiko' class
        start_date (str): date to start search data
        end_date (str): date to end search data
        monkeypatch (MonkeyPatch): the pytest monkeypatch fixture object
        database (Database): an instance of the 'Database' class
    """
    monkeypatch.setattr(Arbiko, 'get_order_history', ArbikoMock.get_order_history)

    assert len(database.session.query(Order).all()) == 0
    assert len(database.session.query(Product).all()) == 0
    assert len(database.session.query(OrderProduct).all()) == 0

    with patch('main.date') as mock_date:
        mock_date.today.return_value = date(2023, 2, 3)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        update_data(database, 'login', 'password', start_date, end_date, 'user_agent')

    mock_arbiko_login.assert_called_once()
    assert len(database.session.query(Order).all()) == 1
    assert len(database.session.query(Product).all()) == 3
    assert len(database.session.query(OrderProduct).all()) == 3


@patch('main.update_data')
def test_refresh_data_if_database_exists(mock_update_data: MagicMock, database: Database):
    """Test 'refresh_data' function if database exists.

    Args:
        mock_update_data (MagicMock): the patched 'update_data' function of the 'main.py' module
        database (Database): an instance of the 'Database' class
    """
    order = Order(order_number=1, date=date(2022, 12, 13))
    database.session.add(order)
    database.session.commit()

    refresh_data(database, 'login0', 'password-99!', 'user-agent')

    mock_update_data.assert_called_once_with(
        database=database,
        login='login0',
        password='password-99!',
        user_agent='user-agent',
        start_date=date(2022, 12, 14)
    )


def test_refresh_data_if_database_doesnt_exists(database: Database):
    """Test case to verify the behavior of the `refresh_data` function when the database doesn't exist.

    Args:
        database (Database): an instance of the 'Database' class
    """
    with pytest.raises(DatabaseError) as error:
        refresh_data(database, 'login0', 'password-99!', 'user-agent')

    assert error.type == DatabaseError
    assert str(error.value) == 'It looks like the database is empty. First, try to update it.'
    assert len(database.session.query(Order).all()) == 0
