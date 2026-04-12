import logging

from flask import Blueprint, render_template, request
from .categories import categories_bp
from .items import items_bp
from .products import products_bp
from .purchase import purchases_bp

logger = logging.getLogger('views')

expenses_bp = Blueprint('expenses', __name__, url_prefix='/v1')
expenses_bp.register_blueprint(categories_bp)
expenses_bp.register_blueprint(items_bp)
expenses_bp.register_blueprint(products_bp)
expenses_bp.register_blueprint(purchases_bp)


@expenses_bp.after_request
def log_ui_request(response):
    logger.info(
        'request handled endpoint=%s status=%s query=%s',
        request.endpoint,
        response.status_code,
        request.query_string.decode('utf-8') or '-'
    )
    return response


@expenses_bp.route('/')
def root():
    return render_template('base.html', active_page='home')


@expenses_bp.route('/catalog')
def catalog_page():
    return render_template('catalog.html', active_page='catalog')


@expenses_bp.route('/purchase/manage')
def purchases_manage_page():
    return render_template('purchases_manage.html', active_page='purchase_manage')


@expenses_bp.route('/item/manage')
def items_manage_page():
    return render_template('items_manage.html', active_page='item_manage')


@expenses_bp.route('/item/report')
def items_report_page():
    return render_template('items_report.html', active_page='item_report')
