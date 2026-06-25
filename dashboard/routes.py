from flask import Blueprint, render_template, redirect, url_for, session
from extensions import db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# صفحه اصلی داشبورد
@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")
