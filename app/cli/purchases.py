import logging
from datetime import datetime

import click

from app.services.database import db


@click.command('edit-shopping')
def edit_shopping():
    try:
        shopping_rows = db.select_all_shopping_trips()
        option = choose_element(
            data_list=[
                f'Store: {shopping["store_name"]} | Purchase date: {shopping["purchase_date"]}'
                for shopping in shopping_rows
            ]
        )
        shopping = shopping_rows[option]

        editable_fields = ['Store name', 'Purchase date', 'Payment method', 'Items']
        selected_field = editable_fields[
            choose_element(data_list=editable_fields, msg='Choose a field to edit:')
        ]

        if selected_field == 'Store name':
            store_name = click.prompt('New store name', type=str)
            purchase_date = shopping['purchase_date']
            payment_method = shopping['payment_method']
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif selected_field == 'Purchase date':
            store_name = shopping['store_name']
            purchase_date = click.prompt('New purchase date (YYYY-MM-DD)', type=str)
            datetime.strptime(purchase_date, '%Y-%m-%d')
            payment_method = shopping['payment_method']
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif selected_field == 'Payment method':
            store_name = shopping['store_name']
            purchase_date = shopping['purchase_date']
            payment_method = click.prompt('New payment method', type=str)
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif selected_field == 'Items':
            ok, msg = change_shopping_items(trip_id=shopping['trip_id'])
        else:
            raise click.ClickException('Invalid field')

        if not ok:
            raise click.ClickException(msg)

        click.echo('Shopping trip updated successfully')
    except ValueError as exc:
        logging.error(exc)
        raise click.ClickException(str(exc))


def change_shopping_items(trip_id):
    items = db.select_purchased_items(trip_id)
    option = choose_element(
        data_list=[
            f'{item["product_name"]} | Brand: {item["brand"]} | Quantity: {item["quantity"]} | Total paid: {item["total_price"]}'
            for item in items
        ],
        msg='Choose the item to edit:'
    )
    item = items[option]

    editable_fields = ['Brand', 'Quantity', 'Total paid']
    selected_field = editable_fields[
        choose_element(data_list=editable_fields, msg='Choose the field to edit:')
    ]

    if selected_field == 'Brand':
        brand = click.prompt('New brand', type=str)
        quantity = item['quantity']
        unit_price = item['unit_price']
    elif selected_field == 'Quantity':
        brand = item['brand']
        quantity = click.prompt('New quantity', type=float)
        unit_price = item['unit_price']
    elif selected_field == 'Total paid':
        brand = item['brand']
        quantity = item['quantity']
        total_price = click.prompt('New total paid', type=float)
        unit_price = total_price / quantity
    else:
        raise click.ClickException('Unrecognized field')

    return db.update_purchased_item(item['item_id'], brand, quantity, unit_price)


def choose_element(data_list=None, msg='') -> int:
    data_list = data_list or []

    if msg:
        click.echo(msg)
    for idx, field in enumerate(data_list):
        click.echo(f'\t{idx}. {field}')

    option = click.prompt('Choose a value', type=int)
    if option < 0 or option >= len(data_list):
        raise click.ClickException('Invalid option')

    return option
