import logging
import app.utils.logs as _
from dotenv import load_dotenv
from flask import Flask

def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.api import expenses_bp
    app.register_blueprint(expenses_bp)

    from app.cli import categories, database, items, products, purchases
    app.cli.add_command(categories.list_categories)
    app.cli.add_command(database.create_tables)
    app.cli.add_command(items.list_purchased_items)
    app.cli.add_command(products.list_products)
    app.cli.add_command(products.register_product)
    app.cli.add_command(purchases.edit_shopping)

    logging.info('application started')

    return app
