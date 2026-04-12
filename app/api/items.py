from http import HTTPStatus

from flask import Blueprint, jsonify
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.responses import error_response
from app.services.database import Session
from app.utils.models import Product, ProductCategory, PurchasedItem

items_bp = Blueprint('items', __name__, url_prefix='/item')


@items_bp.route('/list')
def list_items():
    session = Session()
    try:
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
            .order_by(Product.product_name)
        )
        rows = session.execute(stmt).all()
        payload = [
            {
                'product_name': row.product_name,
                'total_price': float(row.total_price),
                'category_name': row.category_name
            }
            for row in rows
        ]
        return jsonify(payload), HTTPStatus.OK
    except SQLAlchemyError as e:
        return error_response(f'Database error: {str(e)}', HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        session.close()
