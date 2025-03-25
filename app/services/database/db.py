import os
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def get_db_engine():
    if 'db' not in g:
        g.db = create_engine(os.getenv('DB_URL', ''), echo=True)
    return g.db


def get_db_session():
    engine = create_engine(os.getenv('DB_URL', ''), echo=True)
    return Session(engine)
