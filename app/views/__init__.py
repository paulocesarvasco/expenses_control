from flask import Blueprint

expenses = Blueprint('expenses', __name__, url_prefix='/v1')
