from http import HTTPStatus
from flask import request, jsonify
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.utils.models import ShoppingTrip, PurchasedItem
from app.utils.models.product import Product
from . import expenses_bp
from app.services.database import Session, db

import logging
logger = logging.getLogger('views')


@expenses_bp.route('/', methods=['GET'])
def root():
    logger.info('home page accessed')
    return '<p>Control Expenses initial page!</p>'


@expenses_bp.route('/register', methods=['POST'])
def save_purchase():
    s = Session()
    try:
        data = request.get_json()

        required_fields = ['store_name', 'purchase_date', 'items']
        if not all(field in data for field in required_fields):
            logger.error({'error': 'Missing required fields'})
            logger.debug(data)
            return jsonify({'error': 'Missing required fields'}), HTTPStatus.BAD_REQUEST

        trip = ShoppingTrip(
            store_name=data['store_name'],
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        s.add(trip)

        for item_data in data['items']:
            if not all(k in item_data for k in ['product_name', 'quantity', 'unit_price']):
                logger.error({'error': 'Missing required fields'})
                logger.debug(data)
                return jsonify({'error': 'Missing item fields'}), HTTPStatus.BAD_REQUEST

            with db.get_db_engine().connect() as conn:
                stmt = (
                    select(Product).where(Product.product_name == item_data['product_name'])
                )
                product_obj = conn.scalars(stmt).first()

            if product_obj is None:
                raise Exception('product not registered')

            purchased_item = PurchasedItem(
                trip=trip,
                product_id=product_obj.product_id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                brand=item_data.get('brand')
            )
            s.add(purchased_item)

        s.commit()

        return jsonify({
            'message': 'Purchase saved successfully',
            'trip_id': trip.trip_id
        }), HTTPStatus.CREATED

    except ValueError as e:
        s.rollback()
        return jsonify({'error': f'Invalid date format: {str(e)}'}), HTTPStatus.BAD_REQUEST
    except SQLAlchemyError as e:
        s.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        s.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
