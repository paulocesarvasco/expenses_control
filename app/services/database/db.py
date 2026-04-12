import os
from datetime import date, datetime

from flask import g, has_request_context
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, joinedload

from app.utils.models import Product, ProductCategory, PurchasedItem, ShoppingTrip

_ENGINE = None
_SESSION_FACTORY = None
_ENGINE_DB_URL = None


def _get_db_url():
    db_url = os.getenv('DB_URL', '')
    if not db_url:
        raise RuntimeError('DB_URL environment variable is required')
    return db_url


def _get_session_factory():
    global _ENGINE
    global _SESSION_FACTORY
    global _ENGINE_DB_URL

    db_url = _get_db_url()
    if _ENGINE is None or _SESSION_FACTORY is None or _ENGINE_DB_URL != db_url:
        if _ENGINE is not None:
            _ENGINE.dispose()
        _ENGINE = create_engine(db_url, echo=False)
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE)
        _ENGINE_DB_URL = db_url

    return _SESSION_FACTORY


def _create_new_session():
    session_factory = _get_session_factory()
    return session_factory()


def _coerce_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d').date()
    raise ValueError('Invalid date value. Use YYYY-MM-DD')


def get_db_engine():
    _get_session_factory()
    return _ENGINE


def close_db(_exception=None):
    session = g.pop('db_session', None)
    if session is not None:
        session.close()


def shutdown_db():
    global _ENGINE
    global _SESSION_FACTORY
    global _ENGINE_DB_URL

    if has_request_context():
        close_db()

    if _ENGINE is not None:
        _ENGINE.dispose()
        _ENGINE = None
        _SESSION_FACTORY = None
        _ENGINE_DB_URL = None


def get_db_session():
    if has_request_context():
        if 'db_session' not in g:
            g.db_session = _create_new_session()
        return g.db_session
    return _create_new_session()


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


def select_product_catalog():
    with get_db_engine().connect() as conn:
        stmt = (
            select(
                Product.product_id,
                Product.product_name,
                ProductCategory.category_id,
                ProductCategory.category_name
            )
            .join(
                ProductCategory,
                Product.category_id == ProductCategory.category_id
            )
            .order_by(Product.product_name)
        )
        return [row._mapping for row in conn.execute(stmt).all()]


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
    start_date = _coerce_date(start_date)
    end_date = _coerce_date(end_date)
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
            .select_from(ShoppingTrip)
            .join(
                PurchasedItem,
                ShoppingTrip.trip_id == PurchasedItem.trip_id
            )
            .join(
                Product,
                Product.product_id == PurchasedItem.product_id
            )
            .where(
                ShoppingTrip.purchase_date.between(start_date, end_date)
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
            .select_from(PurchasedItem)
            .join(
                Product,
                PurchasedItem.product_id == Product.product_id
            )
            .join(
                ProductCategory,
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
    purchase_date = _coerce_date(purchase_date)
    s = _create_new_session()
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
    finally:
        s.close()


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
    s = _create_new_session()
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
    finally:
        s.close()
