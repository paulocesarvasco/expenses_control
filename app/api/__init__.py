from flask import Blueprint, render_template
from .products import products_bp
from .purchase import purchases_bp


expenses_bp = Blueprint('expenses', __name__, url_prefix='/v1')
expenses_bp.register_blueprint(products_bp)
expenses_bp.register_blueprint(purchases_bp)


@expenses_bp.route('/')
def root():
    return render_template('base.html')
