from flask import Blueprint
from .search import searches_bp
from .register import registers_bp


expenses_bp = Blueprint('expenses', __name__, url_prefix='/v1')
expenses_bp.register_blueprint(registers_bp)
expenses_bp.register_blueprint(searches_bp)

@expenses_bp.route('/')
def root():
    return '<p>Control Expenses initial page!</p>'
