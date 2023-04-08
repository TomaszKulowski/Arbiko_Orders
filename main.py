import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import re

from terminaltables import AsciiTable
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc

from arbiko import load_data, load_data_fake_response
from database import Database
from exceptions import DatabaseError
from models import Orders, Products
from protection import Protection

database_path = Path('db.db')


def load_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--refresh', help='refresh the database', action='store_true')
    group.add_argument('-u', '--update', help='update the database', action='store_true')
    group.add_argument('-s', '--search', help='choose to search data', action='store_true', default=True)
    parser.add_argument('-start_date', help='date format: YYYY-MM-DD')
    parser.add_argument('-end_date', help='date format: YYYY-MM-DD')

    args = parser.parse_args()

    return args


def get_data(start_date=None, end_date=None):
    # set the default date to update database as 1 year
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    # response = load_data('2022-02-22', '2022-02-25')
    # response = load_data(start_date, end_date)
    response = load_data_fake_response()

    for order_number, details in response.items():
        products = 
        order_date = details['date']

        for product in details['products']:
            product_model = Products(
                catalog_number=product['catalog_number'],
                description=product['description'],
            )

            filters = (
                    (Products.catalog_number == product_model.catalog_number) &
                    (Products.oem_number == product_model.oem_number) &
                    (Products.description == product_model.description)
            )

            result = database.session.query(Products).filter(filters).all()
            if len(result) == 1:
                product_id = result[0].id

            elif not result:
                database.session.add(product_model)
                database.session.commit()
                product_id = product_model.id

            else:
                raise ValueError

            products[product_id] = product['quantity']

        order = Orders(
            order_number=order_number,
            date=order_date,
            products=products,
        )
        database.session.add(order)
        database.session.commit()


def refresh_data():
    """The function gets the latest records from arbiko.pl."""
    date_of_last_order = database.session.query(Orders).order_by(desc(Orders.date)).first()
    if date_of_last_order:
        get_data(start_date=date_of_last_order.date + timedelta(days=1))
    else:
        raise DatabaseError('It looks like the database is empty. First, try to update it.')


def search():
    phrase = None
    while phrase != 'exit':
        products = []
        print()
        print('To exit type "exit"')
        print('Search by catalog number/oem number/description')
        # phrases = input('Search: >>> ').strip().lower()
        phrases = 'toner'
        filters = (
            Products.catalog_number,
            Products.oem_number,
            Products.description,
        )
        # todo to verify
        catalog_number = re.compile('[1-9]+ [1-9]+').match(phrases)
        if catalog_number:
            phrases.replace(' ', '')

        for filter in filters:
            for phrase in phrases.split(' '):
                products += database.session.query(Products).filter(filter.like(f'%{phrase}%')).all()

        # print(database.session.query(Orders).filter(Orders.products.contains('1') {'1': '2', '2': '2'}).all())
        a = database.session.query(Orders).filter(Orders.products.contains({'1': '4', '2': '5'})).all()
        for i in a:
            print(i.order_number)
        # a = database.session.query(Orders.products).all()
        # print(a)
        # for product in products:
        #     order = database.session.query(Orders).filter(Orders.products['product_id'] == int(product.id)).all()
        #     print(order)
        phrase = 'exit'


def draw_table(records):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("Order number")
    table.add_column("Date")
    table.add_column("Catalog num")
    table.add_column("Description")
    table.add_column("Amount", justify="right")
    for record in records:
        table.add_row(
            value[0], value[1], value[2], value[3], value[4]
        )

    console.print(table)


if __name__ == '__main__':
    args = load_arguments()

    with Database(database_path) as database:
        if not database_path.exists():
            database.create_database()
        else:
            database.load()

        if args.update:
            try:
                get_data(args.start_date, args.end_date)
            except ValueError as error:
                print(error)

        if args.refresh:
            try:
                refresh_data()
            except DatabaseError as error:
                print(error)

        if args.search:
            search()
            # draw_table(search())
