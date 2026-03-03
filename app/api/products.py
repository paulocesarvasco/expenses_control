from http import HTTPStatus
from flask import Blueprint, jsonify, request
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.services.database import Session, db
from app.utils.models import Product, ProductCategory

logger = logging.getLogger('views')

products_bp = Blueprint('products', __name__, url_prefix='/product')

@products_bp.route('/list')
def list_products():
    try:
        product_list = db.select_all_products()
        return jsonify(product_list), HTTPStatus.OK
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@products_bp.route('/list-detailed')
def list_products_detailed():
    session = Session()
    try:
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
        rows = session.execute(stmt).all()
        payload = [
            {
                'product_id': row.product_id,
                'product_name': row.product_name,
                'category_id': row.category_id,
                'category_name': row.category_name
            }
            for row in rows
        ]
        return jsonify(payload), HTTPStatus.OK
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@products_bp.route('/register', methods=['POST'])
def register_product():
    session = Session()
    try:
        data = request.get_json() or {}
        product_name = str(data.get('product_name', '')).strip()
        if not product_name:
            return jsonify({'error': 'Field "product_name" is required'}), HTTPStatus.BAD_REQUEST

        category_id = data.get('category_id')
        category_name = data.get('category_name')
        if category_id is None and category_name is None:
            return jsonify({'error': 'Provide "category_id" or "category_name"'}), HTTPStatus.BAD_REQUEST

        if category_id is None:
            categories = db.select_all_categories()
            category_id = categories.get(str(category_name))
            if category_id is None:
                return jsonify({'error': 'Category not found'}), HTTPStatus.BAD_REQUEST

        product = Product(product_name=product_name, category_id=category_id)
        session.add(product)
        session.commit()
        return jsonify(
            {
                'message': 'Product registered successfully',
                'product_id': product.product_id,
                'product_name': product.product_name,
                'category_id': product.category_id
            }
        ), HTTPStatus.CREATED

    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Product already exists'}), HTTPStatus.BAD_REQUEST
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@products_bp.route('/register-batch', methods=['POST'])
def register_products_batch():
    payload = request.get_json() or {}
    products = payload.get('products')
    if not isinstance(products, list) or len(products) == 0:
        return jsonify({'error': 'Field "products" must be a non-empty array'}), HTTPStatus.BAD_REQUEST

    categories = db.select_all_categories()
    created = []
    errors = []

    for idx, product_data in enumerate(products):
        session = Session()
        try:
            product_name = str(product_data.get('product_name', '')).strip()
            if not product_name:
                raise ValueError('Field "product_name" is required')

            category_id = product_data.get('category_id')
            if category_id is None:
                category_name = str(product_data.get('category_name', '')).strip()
                category_id = categories.get(category_name)
                if category_id is None:
                    raise ValueError('Category not found')

            product = Product(product_name=product_name, category_id=category_id)
            session.add(product)
            session.commit()
            created.append(
                {
                    'index': idx,
                    'product_id': product.product_id,
                    'product_name': product.product_name
                }
            )
        except IntegrityError:
            session.rollback()
            errors.append({'index': idx, 'error': 'Product already exists'})
        except (ValueError, SQLAlchemyError) as e:
            session.rollback()
            errors.append({'index': idx, 'error': str(e)})
        finally:
            session.close()

    status = HTTPStatus.CREATED if not errors else HTTPStatus.MULTI_STATUS
    return jsonify({'created': created, 'errors': errors}), status
