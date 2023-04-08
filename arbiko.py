import sys
from datetime import datetime
from requests import Session

from bs4 import BeautifulSoup

from credentials import login, password
from models import Order, Product

url = 'http://arbiko.pl/arbos/search_zam.php3?ref=zamowienia'
login_url = 'http://arbiko.pl/arbos/loguj1.php3'
payload = {
    'user': login,
    'passwd': password,
    'Submit': 'Loguj >>'
}


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36 OPR/34.0.2036.42',
}


def load_data(start_date, end_date):
    payload2 = {
        'filters': 'data_od,data_do,numer,stan',
        'data_od': start_date,
        'data_do': end_date,
        'numer_zam': '',
        'stan': '',
        'sbm': 'Szukaj',
    }
    with Session() as session:
        session.headers = headers
        session.post(login_url, data=payload)
        response = session.post(url, data=payload2)

        doc = BeautifulSoup(response.text, 'html.parser')

        table = doc.find_all('table')
        orders = []
        for i in table[3]:
            res = i.find_all()[11]
            try:
                orders.append(str(res).split("'")[1])
            except Exception:
                continue

        data = {}
        for order in orders:
            order_url = 'http://arbiko.pl/arbos/' + order

            content = session.get(order_url)
            order = BeautifulSoup(content.text, 'html.parser')

            tbody = order.tbody
            order_number = order.find_all('p')[1].text.split(' ')[3].strip('Status')
            trs = tbody.contents

            table = order.find_all('table')
            tr = table[2].find_all_next('td')

            order_date = [int(i) for i in tr[-25].text.split('-')]
            order_date = datetime(order_date[0], order_date[1], order_date[2])

            data[order_number] = {'date': order_date}
            data[order_number]['products'] = []
            for value in trs[1:]:
                val = value.find_all('td')[1:]
                try:
                    num, desc, _, quantity, *_ = val
                    product = {
                        'catalog_number': num.text,
                        'description': desc.text,
                        'quantity': quantity.text,
                    }
                    data[order_number]['products'].append(product)

                except Exception:
                    pass
    return data


def load_data_fake_response(*args):
    result = {'420397': {
        'date': datetime(2022, 4, 23),
        'products':
            [
                {
                    'catalog_number': '4455 3256',
                    'description': 'Toner C35P ',
                    'quantity': '4'
                },
                {
                    'catalog_number': '4475 0255',
                    'description': 'Toner kart OKI',
                    'quantity': '5'}]},
                 '420399':
                     {'date': datetime(2022, 3, 29),
                      'products':
                          [
                              {
                                  'catalog_number': '4455 3256',
                                  'description': 'Toner C35P ',
                                  'quantity': '33'
                              },
                              {
                                  'catalog_number': '4475 0255',
                                  'description': 'Toner kart OKI',
                                  'quantity': '3'}]}
                 }
    return result
