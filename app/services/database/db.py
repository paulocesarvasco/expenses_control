import os
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.models import Product, ProductCategory, PurchasedItem, ShoppingTrip
from sqlalchemy import select


def get_db_engine():
    if 'db' not in g:
        g.db = create_engine(os.getenv('DB_URL', ''), echo=False)
    return g.db


def get_db_session():
    engine = create_engine(os.getenv('DB_URL', ''), echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def select_all_categories():
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                ProductCategory.category_name,
                ProductCategory.category_id
            )
            .select_from(
                ProductCategory
            )
        )
        return {str(row[0]):int(row[1]) for row in conn.execute(stmt).all()}


def select_all_products():
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                Product.product_name,
            )
            .select_from(
                Product
            )
        )
        return conn.scalars(stmt).all()


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
                PurchasedItem.unit_price,
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
            .order_by(
                ShoppingTrip.purchase_date.desc()
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


def select_shoppings_by_category():
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                Product.product_name,
                PurchasedItem.total_price,
                ProductCategory.category_name
            )
            .where(
                PurchasedItem.product_id == Product.product_id,
                Product.category_id == ProductCategory.category_id
            )
            .order_by(
                Product.product_name
            )
        )
        res = conn.execute(stmt).all()
    return [r._mapping for r in res]
