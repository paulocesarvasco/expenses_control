from . import expenses_bp
from app.services.database import Session, db
from app.utils.exceptions.custom_exceptions import ProductError, RequestPayloadError
from app.utils.models import ShoppingTrip, PurchasedItem
from app.utils.models.product import Product
from datetime import datetime
from flask import request, jsonify
from http import HTTPStatus
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

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
            raise RequestPayloadError('Missing required fields')

        trip = ShoppingTrip(
            store_name=data['store_name'],
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        total = 0

        for item_data in data['items']:
            if not all(k in item_data for k in ['product_name', 'quantity', 'unit_price']):
                logger.error({'error': 'Missing required fields'})
                logger.debug(data)
                raise RequestPayloadError('Missing item fields')

            with db.get_db_engine().connect() as conn:
                stmt = (
                    select(Product.product_id).where(Product.product_name == item_data['product_name'])
                )
                product_id = conn.scalars(stmt).first()

            if product_id is None:
                raise ProductError('product not registered')

            purchased_item = PurchasedItem(
                trip=trip,
                product_id=product_id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                brand=item_data.get('brand')
            )
            s.add(purchased_item)

            total += purchased_item.quantity * purchased_item.unit_price

        trip.total_amount = total
        s.add(trip)
        s.commit()

        return jsonify({
            'message': 'Purchase saved successfully',
            'trip_id': trip.trip_id
        }), HTTPStatus.CREATED

    except (ProductError, RequestPayloadError, TypeError, ValueError) as e:
        s.rollback()
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except SQLAlchemyError as e:
        s.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        s.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
