from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import User
from auth.utils import hash_password

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/")
def users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    users = User.query.order_by(User.id.desc()).all()
    return render_template("users/index.html", users=users)

@users_bp.route("/create", methods=["GET", "POST"])
def create_user():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        user = User(
            full_name=request.form["full_name"],
            username=request.form["username"],
            mobile=request.form["mobile"],
            is_active=True
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        flash("کاربر با موفقیت ایجاد شد.", "success")
        return redirect(url_for("users.users"))

    return render_template("users/create.html")
