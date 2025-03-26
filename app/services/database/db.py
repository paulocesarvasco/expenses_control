import os
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_db_engine():
    if 'db' not in g:
        g.db = create_engine(os.getenv('DB_URL', ''), echo=False)
    return g.db


def get_db_session():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Session = sessionmaker(bind=engine)
    return Session()
