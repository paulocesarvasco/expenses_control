import logging
import app.utils.logs as _
from dotenv import load_dotenv
from flask import Flask

def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.api import expenses_bp
    app.register_blueprint(expenses_bp)

    from app.cli import database
    app.cli.add_command(database.create_tables)
    app.cli.add_command(database.register_category)
    app.cli.add_command(database.list_categories)
    app.cli.add_command(database.register_product)
    app.cli.add_command(database.list_products)

    print(app.url_map)

    logging.info('application started')

    return app
