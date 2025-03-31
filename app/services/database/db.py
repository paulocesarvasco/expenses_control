import os
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.models import Product, PurchasedItem, ShoppingTrip
from sqlalchemy import select


def get_db_engine():
    if 'db' not in g:
        g.db = create_engine(os.getenv('DB_URL', ''), echo=False)
    return g.db


def get_db_session():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

def select_shopping_trips(start_date, end_date):
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                ShoppingTrip.trip_id,
                ShoppingTrip.store_name,
                ShoppingTrip.purchase_date,
                ShoppingTrip.total_amount,
                Product.product_name,
                PurchasedItem.brand,
                PurchasedItem.total_price,
                PurchasedItem.quantity
            )
            .select_from(
                PurchasedItem,
                ShoppingTrip,
                PurchasedItem
            )
            .where(
                ShoppingTrip.purchase_date.between(start_date, end_date)

            )
            .where(
                ShoppingTrip.trip_id == PurchasedItem.trip_id,
            )
            .where(
                Product.product_id == PurchasedItem.product_id
            )
        )
        return conn.execute(stmt).all()


def select_product_id(product:str):
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                Product.product_id
            )
            .where(
                Product.product_name == product
            )
        )
        return conn.scalars(stmt).first()
