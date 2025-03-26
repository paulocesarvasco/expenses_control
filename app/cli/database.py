import click
import logging
import os

from app.services.database import db
from app.utils.models import Base
from sqlalchemy import create_engine, select
from app.utils.models import ProductCategory

@click.command('init-db')
def create_tables():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Base.metadata.create_all(engine)
    logging.info('Created tables: {}'.format(Base.metadata.tables.keys()))


@click.command('insert-category')
def register_product():
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
        print([r._mapping for r in res])
