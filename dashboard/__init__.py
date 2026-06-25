from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ایمپورت همه فایل‌ها بعد از ساخت بلوپرینت
from . import routes
from . import organizations
from . import channels
from . import posts
from . import bots
from . import platforms
from . import instagram
from . import db_manage
from . import assign
