from datetime import date, datetime

from app.services.database import db
from app.utils.exceptions.custom_exceptions import ProductError, RequestPayloadError
from app.models import PurchasedItem, ShoppingTrip


def parse_iso_date(value: str) -> date:
    return datetime.strptime(str(value), '%Y-%m-%d').date()


def date_to_iso(value) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return parse_iso_date(value).isoformat()
    raise ValueError('Invalid date value')


def create_purchase_from_payload(session, data):
    if not isinstance(data, dict):
        raise RequestPayloadError('Invalid JSON payload')

    required_fields = ['store_name', 'purchase_date', 'items']
    if not all(field in data for field in required_fields):
        raise RequestPayloadError('Missing required fields')

    store_name = str(data['store_name']).strip()
    if not store_name:
        raise RequestPayloadError('Field "store_name" is required')

    items = data['items']
    if not isinstance(items, list) or len(items) == 0:
        raise RequestPayloadError('Field "items" must be a non-empty list')

    payment_method_name = str(data.get('payment_method', '')).strip()
    if not payment_method_name:
        raise RequestPayloadError('Field "payment_method" is required')
    payment_method_id = db.select_payment_method_id(payment_method_name)
    if payment_method_id is None:
        raise RequestPayloadError('Payment method not found')

    trip = ShoppingTrip(
        store_name=store_name.title(),
        purchase_date=parse_iso_date(data['purchase_date']),
        payment_method_id=payment_method_id,
        notes=data.get('notes')
    )

    total = 0.0
    for item_data in items:
        if not isinstance(item_data, dict):
            raise RequestPayloadError('Invalid item payload')
        if not all(k in item_data for k in ['product_name', 'quantity', 'price']):
            raise RequestPayloadError('Missing item fields')

        product_name = str(item_data['product_name']).strip()
        if not product_name:
            raise RequestPayloadError('Field "product_name" is required')

        quantity = float(item_data['quantity'])
        price = float(item_data['price'])
        if quantity <= 0:
            raise RequestPayloadError('Quantity must be greater than zero')
        if price <= 0:
            raise RequestPayloadError('Price must be greater than zero')

        product_id = db.select_product_id(product=product_name)
        if product_id is None:
            raise ProductError('product not registered')

        purchased_item = PurchasedItem(
            trip=trip,
            product_id=product_id,
            quantity=quantity,
            unit_price=(price / quantity),
            brand=item_data.get('brand')
        )
        session.add(purchased_item)
        total += price

    trip.total_amount = total
    session.add(trip)
    return trip


def normalize_purchase_update_payload(data, trip):
    payload = data or {}
    store_name = payload.get('store_name', trip.store_name)
    payment_method_name = payload.get(
        'payment_method',
        trip.payment_method.payment_method_name if trip.payment_method is not None else None
    )
    purchase_date = payload.get('purchase_date', trip.purchase_date)

    if isinstance(purchase_date, str):
        purchase_date = parse_iso_date(purchase_date)
    elif not isinstance(purchase_date, date):
        raise RequestPayloadError('Invalid date format. Use YYYY-MM-DD')

    payment_method_id = None
    if payment_method_name is not None:
        payment_method_id = db.select_payment_method_id(str(payment_method_name).strip())
        if payment_method_id is None:
            raise RequestPayloadError('Payment method not found')

    return store_name, purchase_date, payment_method_id, payment_method_name


def normalize_purchase_item_update_payload(data, item):
    payload = data or {}
    brand = payload.get('brand', item.brand)
    quantity = float(payload.get('quantity', item.quantity))
    if quantity <= 0:
        raise RequestPayloadError('Quantity must be greater than zero')

    if payload.get('unit_price') is not None:
        unit_price = float(payload['unit_price'])
    elif payload.get('total_price') is not None:
        unit_price = float(payload['total_price']) / quantity
    else:
        unit_price = float(item.unit_price)

    if unit_price <= 0:
        raise RequestPayloadError('Unit price must be greater than zero')

    return brand, quantity, unit_price
