"""The module to scrape http://arbiko.pl site."""
from datetime import datetime
from requests import Session

from bs4 import BeautifulSoup

from exceptions import LoginError


class Arbiko:
    """The collections of the tools to scrape arbiko.pl site.
    The class has implemented the necessary methods to use as a context manager.

    Methods:
        login():
        get_order_history(start_date: str, end_date: str): fetches and return the order history
            for the passed time period
        get_oem_number(catalog_number: str): fetches oem number for the passed catalog number
    """
    def __init__(self, username: str, password: str, user_agent: str):
        """Construct all the necessary attributes for the arbiko object.

        Args:
            username (str): username to login in aribko.pl site
            password (str): password to login in aribko.pl site
            user_agent (str): user agent
        """
        self.history_url = 'http://arbiko.pl/arbos/search_zam.php3?ref=zamowienia'
        self.search_url = 'http://arbiko.pl/arbos/search_of.php3?ref=oferta'
        self.login_url = 'http://arbiko.pl/arbos/loguj1.php3'
        self.password = password
        self.username = username

        self.session = None
        self.user_agent = user_agent

    def __enter__(self):
        if not self.login():
            raise LoginError
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _set_headers(self):
        """Set user agent in headers."""
        self.headers = {
            'User-Agent': self.user_agent
        }
        self.session.headers = self.headers

    def login(self) -> bool:
        """The method try to login at aribko.pl.

        Returns:
            True (bool): if login was correct
            False (bool): if login was incorrectly."""
        login_payload = {
            'user': self.username,
            'passwd': self.password,
            'Submit': 'Loguj >>'
        }

        with Session() as self.session:
            self._set_headers()
            self.session.post(self.login_url, data=login_payload)
            if 'logged' in self.session.cookies:
                if self.session.cookies['logged'] == 'yes':
                    return True
            else:
                return False

    def get_order_history(self, start_date: str, end_date: str) -> dict:
        """The method fetches and return the order history
            for the passed time period.

        Args:
            start_date (str): start date to get order history
            end_date (str): end date to get order history

        Returns:
            result (dict): fetched data
        """
        history_payload = {
            'filters': 'data_od,data_do,numer,stan',
            'data_od': start_date,
            'data_do': end_date,
            'numer_zam': '',
            'stan': '',
            'sbm': 'Szukaj',
        }

        response = self.session.post(self.history_url, data=history_payload)

        document = BeautifulSoup(response.text, 'html.parser')

        tables = document.find_all('table')
        orders = []
        for row in tables[3]:
            result = str(row.find_all()[11]).split("'")
            if len(result) > 2:
                orders.append(result[1])

        result = {}
        for order in orders:
            order_url = 'http://arbiko.pl/arbos/' + order

            content = self.session.get(order_url)
            order = BeautifulSoup(content.text, 'html.parser')

            tbody = order.tbody
            order_number = order.find_all('p')[1].text.split(' ')[3].strip('Status')
            trs = tbody.contents

            table = order.find_all('table')
            tr = table[2].find_all_next('td')

            order_date = [int(num) for num in tr[-25].text.split('-')]
            order_date = datetime(order_date[0], order_date[1], order_date[2])

            result[order_number] = {'date': order_date}
            result[order_number]['products'] = []
            for value in trs[1:]:
                details = value.find_all('td')[1:]
                if len(details) > 4:
                    cat_num, desc, _, quantity, *_ = details
                    # The catalog number can't start at zero
                    cat_num_without_zero = cat_num.text[1:] if cat_num.text[0] == '0' else cat_num.text
                    product = {
                        'catalog_number': cat_num.text,
                        'oem_number': self.get_oem_number(cat_num_without_zero),
                        'description': desc.text,
                        'quantity': quantity.text,
                    }
                    result[order_number]['products'].append(product)

        return result

    def get_oem_number(self, catalog_number: str) -> str:
        """The method fetches and return oem number for the passed catalog number.

        Args:
            catalog_number (str): product catalog number to get oem number

        Returns:
            (str): oem number or string "???? ????" if was error
        """
        search_payload = {
            'keyw': catalog_number,
        }

        response = self.session.post(self.search_url, data=search_payload)
        document = BeautifulSoup(response.text, 'html.parser')
        try:
            table = document.find_all('table')[2]
            tr = table.find_all_next('tr')[1]
            td = tr.find_all_next('td')
            oem_numbers = td[1].get_text(separator=' ')

            return oem_numbers

        except IndexError:
            print(f'Problem with product number: {catalog_number}')
            return '???? ????'
