from flask import Blueprint

expenses_bp = Blueprint('expenses', __name__, url_prefix='/v1')
