from datetime import datetime
from http import HTTPStatus
from flask import Blueprint, jsonify, request
from app.services.database import db
from app.utils.models import Product, PurchasedItem, ShoppingTrip
from sqlalchemy import select

from app.utils.models.payloads import SearchResponsePayload

import logging
logger = logging.getLogger('views')

searches_bp = Blueprint('searches', __name__, url_prefix='/search')

@searches_bp.route('/')
def search_purchases():
    try:
        start_date = request.args.get('start', type=str, default='2000-01-01')
        end_date = request.args.get('end', type=str)

        if end_date is None:
            end_date = (datetime.now()).strftime('%Y-%m-%d')

        with db.get_db_engine().connect() as conn:
            stmt = (
                select(
                    ShoppingTrip.store_name,
                    ShoppingTrip.purchase_date,
                    ShoppingTrip.total_amount,
                    Product.product_name,
                    PurchasedItem.brand,
                    PurchasedItem.total_price,
                    PurchasedItem.quantity
                )
                .select_from(
                    PurchasedItem,
                    ShoppingTrip,
                    PurchasedItem
                )
                .where(
                    ShoppingTrip.purchase_date.between(start_date, end_date)
                )
                .where(
                    ShoppingTrip.trip_id == PurchasedItem.trip_id,
                )
                .where(
                    Product.product_id == PurchasedItem.product_id
                )
            )
            trips = conn.execute(stmt).all()

            committed_stores = dict()
            for r in trips:
                try:
                    store_name, date, total, item, brand, price, quantity = r
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


            return jsonify(list_results), HTTPStatus.OK

    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
