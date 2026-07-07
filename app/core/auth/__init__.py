from flask import Blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

from . import routes

def init_module(app):
    limiter.init_app(app)
    app.register_blueprint(auth_bp)
