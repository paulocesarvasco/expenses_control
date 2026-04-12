import click
import logging
import os

from app.utils.models import Base
from sqlalchemy import create_engine


def _get_engine():
    return create_engine(os.getenv('DB_URL', ''), echo=False)


@click.command('init-db')
def create_tables():
    engine = _get_engine()
    Base.metadata.create_all(engine)
    logging.info('Created tables: {}'.format(Base.metadata.tables.keys()))


@click.command('reset-db')
def reset_tables():
    engine = _get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logging.info('Dropped and recreated tables: {}'.format(Base.metadata.tables.keys()))
