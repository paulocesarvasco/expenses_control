import logging
import signal
from http import HTTPStatus

import app.utils.logs as _
from dotenv import load_dotenv
from flask import Flask, request
from werkzeug.exceptions import HTTPException

from app.api.responses import error_response
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

    try:
        signal.signal(signal.SIGINT, _handle_shutdown)
        signal.signal(signal.SIGTERM, _handle_shutdown)
    except ValueError:
        logging.warning('signal handlers can only be registered in the main thread')


def _wants_json_error():
    ui_paths = {
        '/v1/',
        '/v1/catalog',
        '/v1/purchase/register_form',
        '/v1/purchase/search',
        '/v1/purchase/manage',
        '/v1/item/manage',
        '/v1/item/report',
    }
    if request.args.get('format', '').lower() == 'json':
        return True
    if request.method != 'GET':
        return True
    return request.path not in ui_paths


def _register_error_handlers(app):
    @app.errorhandler(Exception)
    def _handle_unexpected_error(exc):
        if isinstance(exc, HTTPException):
            return exc

        logging.exception('unhandled application error on path=%s', request.path)
        if _wants_json_error():
            return error_response('Internal server error', HTTPStatus.INTERNAL_SERVER_ERROR)
        return ('Internal server error', HTTPStatus.INTERNAL_SERVER_ERROR)


def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.api import expenses_bp
    app.register_blueprint(expenses_bp)

    from app.cli import categories, database, items, products, purchases
    app.cli.add_command(categories.register_category)
    app.cli.add_command(categories.list_categories)
    app.cli.add_command(database.create_tables)
    app.cli.add_command(database.reset_tables)
    app.cli.add_command(items.list_purchased_items)
    app.cli.add_command(products.list_products)
    app.cli.add_command(products.register_product)
    app.cli.add_command(purchases.edit_shopping)

    app.teardown_appcontext(db.close_db)
    _register_signal_handlers(app)
    _register_error_handlers(app)

    logging.info('application started')

    return app
