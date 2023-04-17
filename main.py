"""The app to manage the placed orders at arbiko.pl site."""
import argparse
from datetime import date, timedelta
from pathlib import Path
import re

from fake_useragent import UserAgent
from rich.console import Console
from rich.table import Table
from sqlalchemy import desc

from arbiko import Arbiko
from credentials import login, password
from database import Database
from exceptions import DatabaseError, ExitException, LoginError
from models import Order, Product, OrderProduct


def load_arguments():
    """The function init arguments.

    Returns:
        args: parsed arguments
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--refresh', help='refresh the database', action='store_true')
    group.add_argument('-u', '--update', help='update the database', action='store_true')
    group.add_argument('-s', '--search', help='choose to search data', action='store_true', default=True)
    parser.add_argument('-start_date', help='date format: YYYY-MM-DD')
    parser.add_argument('-end_date', help='date format: YYYY-MM-DD')

    args = parser.parse_args()

    return args


def update_data(start_date: str = None, end_date: str = None):
    """The function to update order history in database.

    Args:
        start_date (str): start date to get order history
        end_date (str): end date to get order history
    """
    # set the default date to update database as 1 year
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    with Arbiko(login, password, user_agent) as arbiko:
        order_history = arbiko.get_order_history(start_date, end_date)

    for order_number, details in order_history.items():
        order = Order(
            order_number=order_number,
            date=details['date'],
        )
        database.session.add(order)

        for product in details['products']:
            product_model = Product(
                catalog_number=product['catalog_number'],
                oem_number=product['oem_number'],
                description=product['description'],
            )

            filters = (
                    (Product.catalog_number == product_model.catalog_number) &
                    (Product.oem_number == product_model.oem_number) &
                    (Product.description == product_model.description)
            )

            # check if the product exist in database
            result = database.session.query(Product).filter(filters).all()
            if len(result) == 1:
                product_id = result[0].id

            elif not result:
                database.session.add(product_model)
                database.session.commit()
                product_id = product_model.id

            else:
                raise ValueError

            product_order = OrderProduct(
                order=order,
                product_id=product_id,
                quantity=product['quantity'],
            )
            database.session.add(product_order)

        database.session.commit()


def refresh_data():
    """The function gets the new records from arbiko.pl."""
    date_of_last_order = database.session.query(Order).order_by(desc(Order.date)).first()
    if date_of_last_order:
        update_data(start_date=date_of_last_order.date + timedelta(days=1))
    else:
        raise DatabaseError('It looks like the database is empty. First, try to update it.')


def _sort_result(value):
    """The function to sort record"""
    return value.order.date


def search() -> list:
    """The function gets a phrase and searches for it in the database.

    Returns:
        result(list): with serched data
    """
    print('\nTo exit type "exit"')
    print('Search by catalog number/oem number/description')

    phrases = input('Search: >>> ').strip().lower()
    result = []

    if phrases == 'exit':
        raise ExitException

    filter_queries = (
        Product.oem_number,
        Product.description,
    )

    catalog_number = re.compile('[0-9]{8}|[0-9]{4} [0-9]{4}').match(phrases)
    if catalog_number:
        if ' ' not in phrases:
            phrases = f'{phrases[:4]} {phrases[4:]}'

        result += database.session.query(OrderProduct) \
            .join(Product).join(Order) \
            .filter(Product.catalog_number == phrases) \
            .order_by(Order.date).all()

        return result

    for fq in filter_queries:
        for phrase in phrases.split(' '):
            result += database.session.query(OrderProduct) \
                .join(Product).join(Order).filter(fq.like(f'%{phrase}%'))\
                .order_by(Order.date).all()
    result.sort(key=_sort_result)

    return result


def draw_table(records: list):
    """The function draw the table with passed data"""
    console = Console()
    table = Table(show_header=True, header_style='bold magenta', show_lines=True)
    table.add_column('Order number')
    table.add_column('Date')
    table.add_column('Catalog num')
    table.add_column('Oem num')
    table.add_column('Description')
    table.add_column('Quantity', justify='right')
    for order_product in records:
        table.add_row(
            str(order_product.order.order_number),
            str(order_product.order.date),
            str(order_product.product.catalog_number),
            str(order_product.product.oem_number),
            str(order_product.product.description),
            str(order_product.quantity),
        )

    console.print(table)


if __name__ == '__main__':
    database_path = Path('db.db')
    user_agent = UserAgent().chrome

    args = load_arguments()

    with Database(database_path) as database:
        if not database_path.exists():
            database.create_database()
        else:
            database.load()

        if args.update:
            try:
                update_data(args.start_date, args.end_date)
            except ValueError as error:
                print(error)
            except LoginError as error:
                print(error)

        if args.refresh:
            try:
                refresh_data()
            except DatabaseError as error:
                print(error)

        if args.search:
            try:
                while True:
                    draw_table(search())
            except ExitException:
                pass
