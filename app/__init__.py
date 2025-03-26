import logging
import app.utils.logs as _
from dotenv import load_dotenv
from flask import Flask

def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.cli import database
    app.cli.add_command(database.create_tables)

    logging.info('application started')

    return app
