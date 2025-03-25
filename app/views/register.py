from http import HTTPStatus
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.utils.models import ShoppingTrip, PurchasedItem
from . import expenses
from app.services.database import Session

import logging
logger = logging.getLogger('views')

@expenses.route('/register', methods=['POST'])
def save_purchase():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['store_name', 'purchase_date', 'items']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), HTTPStatus.BAD_REQUEST

        # Create or find shopping trip
        trip = ShoppingTrip(
            store_name=data['store_name'],
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        s = Session()
        s.add(trip)

        # Process each item in the purchase
        for item_data in data['items']:
            # Validate item fields
            if not all(k in item_data for k in ['product_id', 'quantity', 'unit_price']):
                return jsonify({'error': 'Missing item fields'}), 400

            # Create purchased item
            purchased_item = PurchasedItem(
                trip=trip,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                is_on_sale=item_data.get('is_on_sale', False),
                brand=item_data.get('brand')
            )
            db.session.add(purchased_item)

        # Commit transaction
        db.session.commit()

        return jsonify({
            'message': 'Purchase saved successfully',
            'trip_id': trip.trip_id
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
