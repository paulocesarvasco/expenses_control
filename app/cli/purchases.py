import click
from datetime import datetime
import logging

from app.services.database import db


@click.command('edit-shopping')
def edit_shopping():
    try:
        shoppings = db.select_all_shopping_trips()
        option = choose_element(data_list=['Loja: {} | Compra dia: {}'.format(shopping['store_name'], shopping['purchase_date']) for shopping in shoppings])
        shopping = shoppings[option]
        del(shoppings)

        editable_fields = ['Nome da Loja', 'Data de Compra', 'Método de Pagamento', 'Items']
        option = editable_fields[choose_element(data_list=editable_fields, msg='Escolha um campo para editar:')]
        if option == editable_fields[0]:
            store_name = input('Insira novo nome para loja: ')
            purchase_date = shopping['purchase_date']
            payment_method = shopping['payment_method']
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif option == editable_fields[1]:
            store_name = shopping['store_name']
            purchase_date = input('Insira nova data de compra: ')
            datetime.strptime(purchase_date, '%Y-%m-%d')
            payment_method = shopping['payment_method']
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif option == editable_fields[2]:
            store_name = shopping['store_name']
            purchase_date = shopping['purchase_date']
            payment_method = input('Insira novo método de pagamento: ')
            ok, msg = db.update_shopping_trip(shopping['trip_id'], payment_method, purchase_date, store_name)
        elif option == editable_fields[3]:
            ok, msg = change_shopping_items(trip_id=shopping['trip_id'])
        else:
            raise Exception('invalid field')

        if not ok:
            raise Exception(msg)

        click.echo('Compra alterada com sucesso')

    except ValueError as e:
        logging.error(e)
    except Exception as e:
        logging.error(e)


def change_shopping_items(trip_id):
    items =  db.select_purchased_items(trip_id)
    option = choose_element(
        data_list=['{}: ! Marca: {} | Quantidade: {} | Valor Pago: {}'.format(item['product_name'], item['brand'], item['quantity'], item['total_price']) for item in items],
        msg='Escolha o item para editar: '
    )
    item = items[option]
    del(items)

    editable_fields = ['Marca', 'Quantidade', 'Valor Pago']
    option = editable_fields[choose_element(data_list=editable_fields, msg='Selecione o campo para editar: ')]
    if option == editable_fields[0]:
        brand = input('Insira nova marca: ')
        quantity = item['quantity']
        unit_price = item['unit_price']
    elif option == editable_fields[1]:
        brand = item['brand']
        quantity = int(input('Insira nova quantidade: '))
        unit_price = item['unit_price']
    elif option == editable_fields[2]:
        brand = item['brand']
        quantity = item['quantity']
        total_price = float(input('Insira novo valor pago: '))
        unit_price = total_price/quantity
    else:
        raise ValueError('unrecognized field')

    return db.update_purchased_item(item['item_id'], brand, quantity, unit_price)


def choose_element(data_list=[], msg='') -> int:
    click.echo(msg)
    for idx, field in enumerate(data_list):
        click.echo('\t{}. {}'.format(idx, field))

    option = int(input('Insira um valor: '))
    if option < 0 or option >= len(data_list):
        raise ValueError('invalid option')

    return option
