from datetime import datetime
from http import HTTPStatus
from flask import Blueprint, jsonify, request
from app.services.database import db
from app.utils.models import Product, PurchasedItem, ShoppingTrip
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

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
                    ShoppingTrip,
                    PurchasedItem
                )
                .join(
                    PurchasedItem,
                    ShoppingTrip.trip_id == PurchasedItem.trip_id
                )
                .where(
                    ShoppingTrip.purchase_date.between(start_date, end_date)
                )
                .order_by(
                    ShoppingTrip.purchase_date.asc()
                )
            )
            # stmt = (
            #     select(ShoppingTrip)
            #     .where(
            #         ShoppingTrip.purchase_date.between(start_date, end_date)
            #     )
            #     .options(
            #         selectinload(ShoppingTrip.items)  # This eagerly loads all related items
            #     )
            #     .order_by(
            #         ShoppingTrip.purchase_date.desc()
            #     )
            # )

            trips = conn.scalars(stmt).all()
            # trips = session.scalars(stmt).unique().all()

            print(trips)

        result = []
        for trip in trips:
            trip_data = {
                "trip_id": trip.trip_id,
                "store_name": trip.store_name,
                "purchase_date": trip.purchase_date.isoformat(),
                "total_amount": trip.total_amount,
                "payment_method": trip.payment_method,
                "items": []
            }

            for item in trip.items:
                item_data = {
                    "item_id": item.item_id,
                    "product_name": item.product.product_name,
                    "category_name": item.product.category.category_name if item.product.category else None,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.quantity * item.unit_price),
                    "brand": item.brand,
                    "is_on_sale": item.is_on_sale
                }
                trip_data["items"].append(item_data)

            result.append(trip_data)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
