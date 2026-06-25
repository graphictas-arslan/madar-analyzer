from flask import Blueprint

# ابتدا بلوپرینت را تعریف کنید
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# سپس routes.py را ایمپورت کنید
from . import routes
