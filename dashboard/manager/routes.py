from flask import Blueprint, render_template, redirect, url_for, session, flash
from extensions import db
from models import User, Channel, Post

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")

@manager_bp.before_request
def check_permission():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if not user or user.role != "manager":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("auth.login"))

@manager_bp.route("/")
def dashboard():
    channels = Channel.query.all()
    posts = Post.query.order_by(Post.publish_date.desc()).all()
    return render_template("manager/index.html", channels=channels, posts=posts)
