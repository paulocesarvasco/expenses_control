import click
import logging
import os

from app.utils.models import Base
from sqlalchemy import create_engine


@click.command('init-db')
def create_tables():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Base.metadata.create_all(engine)
    logging.info('Created tables: {}'.format(Base.metadata.tables.keys()))
