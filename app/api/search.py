from datetime import datetime
from http import HTTPStatus
from flask import Blueprint, jsonify, render_template, request
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
