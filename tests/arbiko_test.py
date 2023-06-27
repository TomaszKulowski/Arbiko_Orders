"""The collections of the test for the arbiko.py module."""
from datetime import datetime
from json import load
from unittest.mock import patch

import responses

from tools.arbiko import Arbiko


@patch('tools.arbiko.Arbiko.login')
def test_login_if_use_as_context_manager(mock_login):
    """Test the login method is called if the Arbiko class is used as a context manager.

    Args:
        mock_login (): mock login method
    """
    with Arbiko('login', 'password', 'user_agent') as arbiko:
        arbiko

    mock_login.assert_called()


@responses.activate
def test_logged():
    """Test if the login method returns True if logged correctly."""
    login_url = 'http://arbiko.pl/arbos/loguj1.php3'
    headers = {'set-cookie': 'logged=yes'}
    responses.add(responses.POST, login_url, headers=headers)
    arbiko = Arbiko('login', 'password', 'user_agent')

    response = arbiko.login()

    assert response is True


@responses.activate
def test_no_logged():
    """Test if the login method returns False if not logged correctly."""
    login_url = 'http://arbiko.pl/arbos/loguj1.php3'
    headers = {'set-cookie': ''}
    responses.add(responses.POST, login_url, headers=headers)
    arbiko = Arbiko('login', 'wrong_password', 'user_agent')

    response = arbiko.login()

    assert response is False


@patch('tools.arbiko.Arbiko.get_oem_number', return_value='12341234')
@responses.activate
def test_get_order_history(mock_get_oem_number):
    """Test if the get_order_history return expected value.

    Args:
        mock_get_oem_number (): mock get_oem_number method
    """
    login_url = 'http://arbiko.pl/arbos/loguj1.php3'
    history_url = 'http://arbiko.pl/arbos/search_zam.php3?ref=zamowienia'
    order_url = 'http://arbiko.pl/arbos/zob_zam.php3?id=208290'
    headers = {'set-cookie': 'logged=yes'}
    responses.add(responses.POST, login_url, adding_headers=headers)
    with open('tests/expected_response_post_history_url.txt') as file:
        expected_response = file.read()
    responses.add(
        responses.POST,
        history_url,
        headers=headers,
        body=expected_response,
    )
    with open('tests/expected_response_get_order_url.txt') as file:
        expected_response = file.read()
    responses.add(responses.GET, order_url, body=expected_response)

    with Arbiko('login', 'password', 'user_agent') as arbiko:
        response = arbiko.get_order_history('2013-11-29', '2013-11-29')

    with open('tests/expected_result_get_order_history.json') as file:
        expected_result = load(file)

    expected_result['215044']['date'] = datetime(2014, 3, 24)

    assert response == expected_result
    assert mock_get_oem_number.call_count == 3


@responses.activate
def test_get_oem_nuber():
    """Test if the get_oem_number method return expected value."""
    login_url = 'http://arbiko.pl/arbos/loguj1.php3'
    search_url = 'http://arbiko.pl/arbos/search_of.php3?ref=oferta'
    headers = {'set-cookie': 'logged=yes'}
    responses.add(responses.POST, login_url, headers=headers)
    with open('tests/expected_response_post_search_url.txt') as file:
        result = file.read()
    responses.add(responses.POST, search_url, body=result)

    with Arbiko('login', 'password', 'user_agent') as arbiko:
        result = arbiko.get_oem_number('4440 3689')

    assert result == 'N/A RL1-2120-000 RL1-3307-000'
