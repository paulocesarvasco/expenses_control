import os

from flask import g
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, joinedload

from app.utils.models import Product, ProductCategory, PurchasedItem, ShoppingTrip

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


def select_all_shopping_trips():
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                ShoppingTrip
                )
            .order_by(
                ShoppingTrip.purchase_date.desc()
            )
        )
        res = conn.execute(stmt).all()
    return [r._mapping for r in res]


def select_shopping_trip_by_id(trip_id):
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                ShoppingTrip
            )
            .where(
                ShoppingTrip.trip_id == trip_id
            )
            .options(
                joinedload(
                    ShoppingTrip.items
                )
                .joinedload(
                    PurchasedItem.product
                )
            )
            .order_by(
                ShoppingTrip.purchase_date.desc()
            )
        )
        res = conn.execute(stmt).all()
    return [r._mapping for r in res]

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


def select_purchased_items(trip_id:int):
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                PurchasedItem,
                Product.product_name
            )
            .where(
                PurchasedItem.trip_id == trip_id,
            )
            .join(
                Product,
                PurchasedItem.product_id == Product.product_id
            )
        )
        res = conn.execute(stmt).all()
    return [r._mapping for r in res]


# def update_store_name(trip_id: int, new_store_name: str):
#     s = get_db_session()
#     try:
#         with s.begin():
#             stmt = (
#                 update(ShoppingTrip)
#                 .where(ShoppingTrip.trip_id == trip_id)
#                 .values(store_name=new_store_name)
#                 .execution_options(synchronize_session="fetch")
#             )
#             result = s.execute(stmt)

#             if result.rowcount == 0:
#                 return False, f"No shopping trip found with ID {trip_id}"

#         return True, f"Successfully updated store name for trip {trip_id}"

#     except SQLAlchemyError as e:
#         s.rollback()
#         return False, f"Error updating store name: {str(e)}"


def update_shopping_trip(trip_id, payment_method, purchase_date, store_name):
    s = get_db_session()
    try:
        with s.begin():
            stmt = (
                update(
                    ShoppingTrip
                )
                .where(
                    ShoppingTrip.trip_id == trip_id
                )
                .values(
                    payment_method=payment_method,
                    purchase_date=purchase_date,
                    store_name=store_name
                )
                .execution_options(synchronize_session="fetch")
            )
            result = s.execute(stmt)

            if result.rowcount == 0:
                return False, f"No shopping trip found with ID {trip_id}"

        return True, f"Successfully updated shopping trip {trip_id}"

    except SQLAlchemyError as e:
        s.rollback()
        return False, f"Error updating shopping trip: {str(e)}"


# def update_payment_method(trip_id: int, new_payment_method: str):
#     s = get_db_session()
#     try:
#         with s.begin():
#             stmt = (
#                 update(ShoppingTrip)
#                 .where(ShoppingTrip.trip_id == trip_id)
#                 .values(payment_method=new_payment_method)
#                 .execution_options(synchronize_session="fetch")
#             )
#             result = s.execute(stmt)

#             if result.rowcount == 0:
#                 return False, f"No shopping trip found with ID {trip_id}"

#         return True, f"Successfully updated payment_method for trip {trip_id}"

#     except SQLAlchemyError as e:
#         s.rollback()
#         return False, f"Error updating payment_method: {str(e)}"

def update_purchased_item(item_id, brand, quantity, unit_price):
    s = get_db_session()
    try:
        with s.begin():
            stmt = (
                update(PurchasedItem)
                .where(PurchasedItem.item_id == item_id)
                .values(
                    brand=brand,
                    quantity=quantity,
                    unit_price=unit_price
                )
                .execution_options(synchronize_session="fetch")
            )
            result = s.execute(stmt)

            if result.rowcount == 0:
                return False, f"No purchased item found with ID {item_id}"

        return True, f"Successfully updated purchased item {item_id}"

    except SQLAlchemyError as e:
        s.rollback()
        return False, f"Error updating item: {str(e)}"
