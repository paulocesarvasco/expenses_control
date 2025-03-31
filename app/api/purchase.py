from app.services.database import Session, db
from app.utils.exceptions.custom_exceptions import ProductError, RequestPayloadError
from app.utils.models import ShoppingTrip, PurchasedItem
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError

from app.utils.models.payloads import SearchResponsePayload

import logging
logger = logging.getLogger('views')

purchases_bp = Blueprint('purchases', __name__, url_prefix='/purchase')

@purchases_bp.route('/register_form')
def get_registry_form():
    return render_template('register.html')


@purchases_bp.route('/save', methods=['POST'])
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


            product_id = db.select_product_id(product=item_data['product_name'])
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


@purchases_bp.route('/search')
def search_purchases():
    try:
        start_date = request.args.get('start', type=str, default='2000-01-01')
        end_date = request.args.get('end', type=str)

        if end_date is None:
            end_date = (datetime.now()).strftime('%Y-%m-%d')

        trips = db.select_shopping_trips(start_date, end_date)
        committed_stores = dict()
        for trip in trips:
            try:
                store_name, date, total, item, brand, price, quantity = trip
                res = SearchResponsePayload()
                key_store = '{}+{}'.format(store_name, date)
                if key_store not in committed_stores.keys():
                    res.store_name = store_name
                    res.purchase_date = date
                    res.total = total
                    committed_stores['{}+{}'.format(store_name, date)] = res
                else:
                    res = committed_stores['{}+{}'.format(store_name, date)]

                purchase = dict()
                purchase['brand'] = brand
                purchase['item'] = item
                purchase['price'] = price
                purchase['quantity'] = quantity
                res.purchases.append(purchase)

            except Exception as e:
                logger.error('failed to generate response payload')
                raise e


        list_results = []
        for _, data in committed_stores.items():
            list_results.append(data.to_dict())


        # return jsonify(list_results), HTTPStatus.OK
        return render_template('search.html', data=list_results)

    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
