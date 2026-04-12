from http import HTTPStatus

from flask import Blueprint, jsonify, request
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.responses import error_response
from app.services.database import Session
from app.utils.models import ProductCategory

categories_bp = Blueprint('categories', __name__, url_prefix='/category')
logger = logging.getLogger('views')


@categories_bp.route('/list')
def list_categories():
    session = Session()
    try:
        stmt = select(
            ProductCategory.category_id,
            ProductCategory.category_name
        ).order_by(ProductCategory.category_name)
        rows = session.execute(stmt).all()
        payload = [
            {
                'category_id': row.category_id,
                'category_name': row.category_name
            }
            for row in rows
        ]
        return jsonify(payload), HTTPStatus.OK
    except SQLAlchemyError as e:
        logger.exception('list_categories database error')
        return error_response(f'Database error: {str(e)}', HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        session.close()


@categories_bp.route('/register', methods=['POST'])
def register_category():
    session = Session()
    try:
        data = request.get_json() or {}
        category_name = str(data.get('category_name', '')).strip()
        if not category_name:
            return error_response('Field "category_name" is required', HTTPStatus.BAD_REQUEST)

        category = ProductCategory(category_name=category_name)
        session.add(category)
        session.commit()
        return jsonify(
            {
                'message': 'Category registered successfully',
                'category_id': category.category_id,
                'category_name': category.category_name
            }
        ), HTTPStatus.CREATED

    except IntegrityError:
        session.rollback()
        logger.info('register_category integrity error: category already exists')
        return error_response('Category already exists', HTTPStatus.BAD_REQUEST)
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception('register_category database error')
        return error_response(f'Database error: {str(e)}', HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        session.close()
