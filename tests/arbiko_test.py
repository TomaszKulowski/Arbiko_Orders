"""The collections of the test for the arbiko.py module."""
from dataclasses import dataclass
from datetime import datetime
from json import load
from unittest.mock import patch
from requests import Session
from pathlib import Path

import pytest
import responses

from tools.arbiko import Arbiko
from tools.exceptions import LoginError


@dataclass
class ArbikoUrls:
    """Dataclass with the Arbiko urls."""
    login_url: str = 'http://arbiko.pl/arbos/loguj1.php3'
    history_url: str = 'http://arbiko.pl/arbos/search_zam.php3?ref=zamowienia'
    order_url: str = 'http://arbiko.pl/arbos/zob_zam.php3?id=208290'
    search_url: str = 'http://arbiko.pl/arbos/search_of.php3?ref=oferta'


class RequestMock(object):
    """Mock request method.

    Methods:
        post(*args, **kwargs): mock the post method in the Session object.
    """
    def __init__(self, *args, **kwargs):
        self.cookies = {}

    def post(self, *args, **kwargs):
        """Mock the post method in the Session object.

        Args:
            *args: various arguments
            **kwargs: various keyword arguments
        """
        if args[0] == ArbikoUrls.login_url:
            if kwargs['data']['passwd'] == 'incorrect_password':
                self.cookies = {'logged': ''}
            elif kwargs['data']['passwd'] == 'correct_password':
                self.cookies = {'logged': 'yes'}


@pytest.fixture()
def no_requests(monkeypatch):
    """Fixture for patching the 'post' and the 'request' methods of the Session class
        to mock HTTP requests.

    Args:
        monkeypatch: the pytest monkeypatch fixture object
    """
    monkeypatch.setattr(Session, 'post', RequestMock.post)
    monkeypatch.setattr(Session, 'request', RequestMock)


@pytest.fixture(params=['incorrect_password', 'correct_password'], name='arbiko')
def fixture_arbiko(request):
    """Fixture for creating an instance of Arbiko with different password parameters.

    Args:
        request: The pytest request object
    """
    arbiko = Arbiko('login', request.param, 'user_agent')

    return arbiko


@patch('tools.arbiko.Arbiko.login', return_value=True)
def test_login_if_use_as_context_manager_correct_pass(mock_login, no_requests):
    """Test case for succesful login using Arbiko as a context manager
        with the correct password.

    Args:
        mock_login: the patched 'login' method of the Arbiko class
        no_requests: fixutre for mocking HTTP requests
    """
    with Arbiko('login', 'correct_password', 'user_agent') as arbiko:
        pass

    mock_login.assert_called()


@patch('tools.arbiko.Arbiko.login', return_value=False)
def test_login_if_use_as_context_manager_incorrect_pass(mock_login, no_requests):
    """Test case for handling a failed login using Arbiko as a context manager
        with an incorrect password.

    Args:
        mock_login: the patched 'login' method of the Arbiko class
        no_requests: fixture for mocking HTTP requests
    """
    with pytest.raises(LoginError) as error:
        with Arbiko('login', 'incorrect_password', 'user_agent') as arbiko:
            pass

    assert error.type == LoginError
    mock_login.assert_called()


def test_login(arbiko, no_requests):
    """Test case for the login method of the Arbiko class.

    Args:
        arbiko(Arbiko): an instance of the Arbiko class
        no_requests: fixture for mocking HTTP requests
        """
    response = arbiko.login()
    if arbiko.password == 'incorrect_password':
        assert response is False

    if arbiko.password == 'correct_password':
        assert response is True


@responses.activate
@patch('tools.arbiko.Arbiko.get_oem_number', return_value='12341234')
def test_parse_server_responses(mock_get_oem_number):
    """Test case for parsing responses from the Arbiko server. 

    Args:
        mock_get_oem_number: the patched 'get_oem_number' method of the Arbiko class
    """
    headers = {'set-cookie': 'logged=yes'}
    responses.add(responses.POST, ArbikoUrls.login_url, adding_headers=headers)
    with open('tests/expected_response_post_history_url.txt') as file:
        expected_response = file.read()
    responses.add(
        responses.POST,
        ArbikoUrls.history_url,
        headers=headers,
        body=expected_response,
    )
    with open('tests/expected_response_get_order_url.txt') as file:
        expected_response = file.read()
    responses.add(responses.GET, ArbikoUrls.order_url, body=expected_response)

    with Arbiko('login', 'correct_password', 'user_agent') as arbiko:
        response = arbiko.get_order_history('2013-11-29', '2013-11-29')

    with open('tests/expected_result_get_order_history.json') as file:
        expected_result = load(file)

    expected_result['215044']['date'] = datetime(2014, 3, 24)

    assert response == expected_result
    assert mock_get_oem_number.call_count == 3


@pytest.mark.parametrize(
    'catalog_number, expected_result',
    (
        ('4440 3689', 'N/A RL1-2120-000 RL1-3307-000'),
        ('0000 0000', '???? ????')
    )
)
@responses.activate
def test_get_oem_number(catalog_number, expected_result, capsys):
    """Test case for retrieving the OEM number for a given catalog number.

    Args:
        catalog_number (str): the catalog number to retrieving the OEM number for
        expected_result: the expected OEM number for the given catalog number
        capsys: the built-in pytest fixture for capturing stdout and stderr
    """
    headers = {'set-cookie': 'logged=yes'}
    responses.add(responses.POST, ArbikoUrls.login_url, headers=headers)
    if expected_result != '???? ????':
        input_file = Path('tests/expected_good_response_post_search_url.txt')
    else:
        input_file = Path('tests/expected_wrong_response_post_search_url.txt')

    with open(input_file) as file:
        result = file.read()
    responses.add(responses.POST, ArbikoUrls.search_url, body=result)

    with Arbiko('login', 'password', 'user_agent') as arbiko:
        result = arbiko.get_oem_number(catalog_number)
    out, err = capsys.readouterr()

    if expected_result == '???? ????':
        assert out == 'Problem with product number: 0000 0000\n'
    assert result == expected_result
