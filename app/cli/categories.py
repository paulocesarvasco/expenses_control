import click
import logging

from app.services.database import db
from sqlalchemy import select
from app.utils.models import ProductCategory
from prettytable import PrettyTable


@click.command('insert-category')
def register_category():
    s = db.get_db_session()
    must_commit = False
    while True:
        try:
            print('Chose an option:')
            print('\t1. Add new product category')
            print('\t2. Save and quit')
            option = int(input('\tOption: '))
            if option == 2:
                if must_commit:
                    s.commit()
                break
            elif option != 1:
                print('invalid option')
                continue

            name = input('Insert category name: ')
            category = ProductCategory(
                category_name=name
            )
            s.add(category)
            must_commit = True
        except Exception as e:
            logging.error(e)
    s.close()


@click.command('list-categories')
def list_categories():
    with db.get_db_engine().connect() as conn:
        stmt = (select(ProductCategory.category_name.label('categoria')))
        res = conn.execute(stmt).all()
        cats = [cat for r in res for cat in r]

        table = PrettyTable()
        table.add_column('Categorias', column=cats)
        print(table)
