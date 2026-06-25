from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ایمپورت مسیرها از routes.py
from . import routes
