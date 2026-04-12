import csv
import logging

import click
from prettytable import PrettyTable

from app.services.database import db
from app.utils.models import Product


def _prompt_product_name() -> str:
    product_name = click.prompt('Product name', type=str).strip()
    if not product_name:
        raise click.ClickException('Product name cannot be empty')
    return product_name


def _choose_category(category_rows) -> int:
    click.echo('Choose the product category ("-1" to abort):')
    for index, row in enumerate(category_rows):
        click.echo(f'\t{index}. {row["category_name"]}')

    selection = click.prompt('Category', type=int)
    if selection == -1:
        return selection
    if selection < 0 or selection >= len(category_rows):
        raise click.ClickException('Invalid category option')
    return selection


def _create_product(session, product_name: str, category_id: int) -> None:
    session.add(Product(product_name=product_name, category_id=category_id))


def _register_product_interactive() -> None:
    session = db.get_db_session()
    category_map = db.select_all_categories()
    if not category_map:
        raise click.ClickException('Register at least one category before adding products')

    categories = [
        {'category_id': category_id, 'category_name': category_name}
        for category_name, category_id in sorted(category_map.items(), key=lambda item: item[0])
    ]

    try:
        while True:
            click.echo('Choose an option:')
            click.echo('\t1. Add new product')
            click.echo('\t2. Save and quit')
            option = click.prompt('Option', type=int)

            if option == 2:
                session.commit()
                click.echo('Products saved')
                return
            if option != 1:
                click.echo('Invalid option')
                continue

            selection = _choose_category(categories)
            if selection == -1:
                click.echo('Operation aborted')
                continue

            category_id = categories[selection]['category_id']
            _create_product(session, _prompt_product_name(), category_id)
    except Exception as exc:
        session.rollback()
        logging.error(exc)
        raise
    finally:
        session.close()


def _register_products_from_file(file_path: str) -> None:
    click.echo('Reading from CSV file')
    categories = db.select_all_categories()

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')
            header = next(reader)
            if len(header) != 2:
                raise click.ClickException(f'Expected 2 columns, got {len(header)}')

            for row in reader:
                if len(row) != 2:
                    raise click.ClickException(f'Row has {len(row)} columns, expected 2')

                session = db.get_db_session()
                try:
                    category_id = categories[row[1]]
                    _create_product(session, row[0], category_id)
                    session.commit()
                except KeyError:
                    session.rollback()
                    click.echo(f'Unknown category: {row[1]}', err=True)
                except Exception as exc:
                    session.rollback()
                    click.echo(str(exc), err=True)
                finally:
                    session.close()
    except FileNotFoundError:
        raise click.ClickException(f"File '{file_path}' not found")


@click.command('list-products')
def list_products():
    product_rows = db.select_product_catalog()

    table = PrettyTable()
    table.add_column('Product', [row['product_name'] for row in product_rows])
    table.add_column('Category', [row['category_name'] for row in product_rows])
    click.echo(table)


@click.command('register-product')
@click.option('-f', default=None, help='Path to CSV file')
def register_product(f):
    logging.info('register product operation started')
    if f is None:
        _register_product_interactive()
        return
    _register_products_from_file(f)
