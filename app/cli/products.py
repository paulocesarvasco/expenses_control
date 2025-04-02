import click
import csv
import logging

from app.services.database import db
from sqlalchemy import select
from app.utils.models import Product, ProductCategory
from prettytable import PrettyTable


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
        res = [r._mapping for r in res]
        prod_list = [prod.get('product_name') for prod in res]
        cat_list = [prod.get('category_name') for prod in res]

        table = PrettyTable()
        table.add_column('Produtos', column=prod_list)
        table.add_column('Categorias', column=cat_list)
        click.echo(table)


@click.command('register-product')
@click.option('-f', default=None, help='Path to csv file')
def register_product(f):
    logging.info('Register product operation started')
    if f is None:
        register_product_interactvement()
    else:
        register_product_from_file(f)


def register_product_interactvement():
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
                        if category >= len(res) or category < -1:
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


def register_product_from_file(file_path):
    click.echo('reading from csv file')
    try:
        cats = db.select_all_categories()
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')
            header = next(reader)
            if len(header) != 2:
                raise ValueError(f"Expected 2 columns, got {len(header)}")


            for row in reader:
                if len(row) != 2:
                    raise ValueError(f"Row has {len(row)} columns, expected 2")
                s = db.get_db_session()
                try:
                    product = Product(
                        product_name = row[0],
                        category_id = cats[row[1]]
                    )
                    s.add(product)
                    s.commit()
                except Exception as e:
                    click.echo(e, err=True)
                    s.rollback()
                finally:
                    s.close()
    except FileNotFoundError as e:
        logging.error('file \'{}\' not found'.format(file_path))
    except Exception as e:
        logging.error('unexpected error to register products: {}'.format(e))
