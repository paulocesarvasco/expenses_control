from http import HTTPStatus
from flask import Blueprint, jsonify
import logging

from app.services.database import db

logger = logging.getLogger('views')

products_bp = Blueprint('products', __name__, url_prefix='/product')

@products_bp.route('/list')
def list_products():
    try:
        product_list = db.select_all_products()
        return jsonify(product_list), HTTPStatus.OK
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
