from flask import render_template, redirect, url_for, session
from . import dashboard_bp

@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")
