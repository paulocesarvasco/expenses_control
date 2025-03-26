import click
import logging
import os

from app.services.database import db
from app.utils.models import Base
from sqlalchemy import create_engine, select
from app.utils.models import Product, ProductCategory


@click.command('init-db')
def create_tables():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Base.metadata.create_all(engine)
    logging.info('Created tables: {}'.format(Base.metadata.tables.keys()))


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
        print([r._mapping for r in res])


@click.command('register-product')
def register_product():
    logging.info('Register product operation started')
    s = db.get_db_session()
    must_commit = False
    while True:
        try:
            print('Choose an option:')
            print('\t1. Add new product')
            print('\t2. Save and quit')
            option = int(input('\tOption: '))

            if option == 2:
                if must_commit:
                    s.commit()
                break
            elif option != 1:

                print('invalid option')
                continue

            while True:
                try:
                    print('Choose the product category (choose "-1" to abort):')
                    with db.get_db_engine().connect() as conn:
                        stmt = (select(ProductCategory.category_id, ProductCategory.category_name))
                        res = conn.execute(stmt).all()
                        for idx in range(len(res)):
                            print('{}. {}'.format(idx, res[idx][1]))


                        category = int(input('Choose product category: '))
                        if category >= len(res) - 1 or category < -1:
                            logging.error('invalid option')
                        else:
                            break
                except Exception as e:
                    logging.error(e)

            if category == -1:
                logging.info('Operation aborted!')
                continue

            name = input('Insert product name: ')
            product = Product(
                product_name=name,
                category_id=res[category][0]
            )
            s.add(product)
            must_commit = True
        except Exception as e:
            logging.error(e)
    s.close()


@click.command('list-products')
def list_products():
    with db.get_db_engine().connect() as conn:
        stmt = select(
            Product.product_name,
            ProductCategory.category_name
        ).join(
            ProductCategory,
            Product.category_id == ProductCategory.category_id
        )
        res = conn.execute(stmt).all()
        print([r._mapping for r in res])
