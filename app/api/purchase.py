from app.services.database import Session, db
from app.services.purchase_service import (
    create_purchase_from_payload,
    date_to_iso,
    normalize_purchase_item_update_payload,
    normalize_purchase_update_payload,
    parse_iso_date,
)
from app.utils.exceptions.custom_exceptions import ProductError, RequestPayloadError
from app.utils.models import Product, PurchasedItem, ShoppingTrip
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from http import HTTPStatus
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.utils.models.payloads import SearchResponsePayload

import logging
logger = logging.getLogger('views')

purchases_bp = Blueprint('purchases', __name__, url_prefix='/purchase')


@purchases_bp.route('/register_form')
def get_registry_form():
    return render_template('register.html', active_page='register')


@purchases_bp.route('/save', methods=['POST'])
def save_purchase():
    s = Session()
    try:
        data = request.get_json()
        trip = create_purchase_from_payload(s, data)
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
    finally:
        s.close()


@purchases_bp.route('/search')
def search_purchases():
    try:
        start_date = request.args.get('start', type=str, default='2000-01-01')
        end_date = request.args.get('end', type=str)

        if end_date is None:
            end_date = (datetime.now()).strftime('%Y-%m-%d')

        start_date = parse_iso_date(start_date)
        end_date = parse_iso_date(end_date)

        trips = db.select_shopping_trips(start_date, end_date)
        committed_trips = dict()
        for trip in trips:
            try:
                trip_id, store_name, purchase_date, total_amount, product_name, brand, unit_price, quantity = trip
                res = SearchResponsePayload()
                if trip_id not in committed_trips.keys():
                    res.store_name = store_name
                    res.purchase_date = datetime.strptime(
                        date_to_iso(purchase_date), '%Y-%m-%d'
                    ).strftime('%d-%m-%Y')
                    res.total = total_amount
                    committed_trips[trip_id] = res
                else:
                    res = committed_trips[trip_id]

                purchase = dict()
                purchase['brand'] = brand
                purchase['item'] = product_name
                purchase['price'] = unit_price
                purchase['quantity'] = quantity
                res.purchases.append(purchase)

            except Exception as e:
                logger.error('failed to generate response payload')
                raise e


        list_results = []
        for _, data in committed_trips.items():
            list_results.append(data.to_dict())


        # return jsonify(list_results), HTTPStatus.OK
        return render_template('search.html', data=list_results, active_page='search')

    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@purchases_bp.route('/list')
def list_purchases():
    session = Session()
    try:
        stmt = (
            select(
                ShoppingTrip.trip_id,
                ShoppingTrip.store_name,
                ShoppingTrip.purchase_date,
                ShoppingTrip.payment_method,
                ShoppingTrip.total_amount
            )
            .order_by(ShoppingTrip.purchase_date.desc())
        )
        rows = session.execute(stmt).all()
        payload = [
            {
                'trip_id': row.trip_id,
                'store_name': row.store_name,
                'purchase_date': date_to_iso(row.purchase_date),
                'payment_method': row.payment_method,
                'total_amount': float(row.total_amount) if row.total_amount is not None else 0.0
            }
            for row in rows
        ]
        return jsonify(payload), HTTPStatus.OK
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@purchases_bp.route('/<int:trip_id>/items')
def list_purchase_items(trip_id):
    session = Session()
    try:
        stmt = (
            select(
                PurchasedItem.item_id,
                PurchasedItem.trip_id,
                Product.product_name,
                PurchasedItem.brand,
                PurchasedItem.quantity,
                PurchasedItem.unit_price,
                PurchasedItem.total_price
            )
            .join(
                Product,
                PurchasedItem.product_id == Product.product_id
            )
            .where(PurchasedItem.trip_id == trip_id)
        )
        rows = session.execute(stmt).all()
        payload = [
            {
                'item_id': row.item_id,
                'trip_id': row.trip_id,
                'product_name': row.product_name,
                'brand': row.brand,
                'quantity': float(row.quantity),
                'unit_price': float(row.unit_price),
                'total_price': float(row.total_price)
            }
            for row in rows
        ]
        return jsonify(payload), HTTPStatus.OK
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@purchases_bp.route('/<int:trip_id>', methods=['PATCH'])
def update_purchase(trip_id):
    session = Session()
    try:
        trip = session.get(ShoppingTrip, trip_id)
        if trip is None:
            return jsonify({'error': f'No shopping trip found with ID {trip_id}'}), HTTPStatus.NOT_FOUND

        store_name, purchase_date, payment_method = normalize_purchase_update_payload(
            request.get_json() or {},
            trip
        )

        ok, msg = db.update_shopping_trip(trip_id, payment_method, purchase_date, store_name)
        if not ok:
            return jsonify({'error': msg}), HTTPStatus.BAD_REQUEST

        return jsonify(
            {
                'message': msg,
                'trip_id': trip_id,
                'store_name': store_name,
                'purchase_date': date_to_iso(purchase_date),
                'payment_method': payment_method
            }
        ), HTTPStatus.OK
    except (ValueError, RequestPayloadError) as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@purchases_bp.route('/item/<int:item_id>', methods=['PATCH'])
def update_purchase_item(item_id):
    session = Session()
    try:
        item = session.get(PurchasedItem, item_id)
        if item is None:
            return jsonify({'error': f'No purchased item found with ID {item_id}'}), HTTPStatus.NOT_FOUND

        brand, quantity, unit_price = normalize_purchase_item_update_payload(
            request.get_json() or {},
            item
        )

        ok, msg = db.update_purchased_item(item_id, brand, quantity, unit_price)
        if not ok:
            return jsonify({'error': msg}), HTTPStatus.BAD_REQUEST

        return jsonify(
            {
                'message': msg,
                'item_id': item_id,
                'brand': brand,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': quantity * unit_price
            }
        ), HTTPStatus.OK
    except (ValueError, RequestPayloadError) as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except SQLAlchemyError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()
