import click
from prettytable import PrettyTable

from app.services.database import db


@click.command('list-items')
def list_purchased_items():
    res = db.select_shoppings_by_category()
    purchased_products = [r.get('product_name') for r in res]
    price_products = [r.get('total_price') for r in res]
    category_products = [r.get('category_name') for r in res]

    table = PrettyTable()
    table.add_column('Product', column=purchased_products)
    table.add_column('Price', column=price_products)
    table.add_column('Category', column=category_products)

    print(table)
