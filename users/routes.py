from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import request
from flask import flash

from extensions import db
from auth.utils import hash_password
from models.user import User


users_bp = Blueprint(
    "users",
    __name__
)

@users_bp.route("/users/create", methods=["GET", "POST"])
def create_user():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        user = User(
            full_name=request.form["full_name"],
            username=request.form["username"],
            mobile=request.form["mobile"],
            password_hash=hash_password(
                request.form["password"]
            ),
            is_active=True
        )

        db.session.add(user)
        db.session.commit()

        flash("کاربر با موفقیت ایجاد شد.")

        return redirect(
            url_for("users.users")
        )

    return render_template(
        "users/create.html"
    )

@users_bp.route("/users")
def users():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "users/index.html",
        users=users
    )
