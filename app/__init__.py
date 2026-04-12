import logging
import signal

import app.utils.logs as _
from dotenv import load_dotenv
from flask import Flask
from app.services.database import db


def _register_signal_handlers(app):
    def _handle_shutdown(signum, _frame):
        signal_name = signal.Signals(signum).name
        logging.info('received %s, shutting down gracefully', signal_name)
        try:
            with app.app_context():
                db.shutdown_db()
        finally:
            raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)


def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.api import expenses_bp
    app.register_blueprint(expenses_bp)

    from app.cli import categories, database, items, products, purchases
    app.cli.add_command(categories.register_category)
    app.cli.add_command(categories.list_categories)
    app.cli.add_command(database.create_tables)
    app.cli.add_command(items.list_purchased_items)
    app.cli.add_command(products.list_products)
    app.cli.add_command(products.register_product)
    app.cli.add_command(purchases.edit_shopping)

    app.teardown_appcontext(db.close_db)
    _register_signal_handlers(app)

    logging.info('application started')

    return app
