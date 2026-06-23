from flask import Blueprint, render_template, redirect, url_for, session

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")

@dashboard_bp.route("/organizations")
def organizations():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/organizations.html")

@dashboard_bp.route("/channels")
def channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/channels.html")

@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/posts.html")
