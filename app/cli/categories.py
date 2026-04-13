import logging

import click
from prettytable import PrettyTable

from app.services.database import db
from app.models import ProductCategory


def _prompt_category_name() -> str:
    category_name = click.prompt('Category name', type=str).strip()
    if not category_name:
        raise click.ClickException('Category name cannot be empty')
    return category_name


def _register_category() -> None:
    session = db.get_db_session()
    try:
        while True:
            click.echo('Choose an option:')
            click.echo('\t1. Add new category')
            click.echo('\t2. Save and quit')
            option = click.prompt('Option', type=int)

            if option == 2:
                session.commit()
                click.echo('Categories saved')
                return
            if option != 1:
                click.echo('Invalid option')
                continue

            category = ProductCategory(category_name=_prompt_category_name())
            session.add(category)
    except Exception as exc:
        session.rollback()
        logging.error(exc)
        raise
    finally:
        session.close()


@click.command('register-category')
def register_category():
    _register_category()


@click.command('insert-category')
def register_category_legacy():
    _register_category()


@click.command('list-categories')
def list_categories():
    categories = db.select_all_categories()

    table = PrettyTable()
    table.add_column('Category', list(categories.keys()))
    click.echo(table)
