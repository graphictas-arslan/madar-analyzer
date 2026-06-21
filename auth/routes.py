from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session

from models.user import User
from auth.utils import verify_password


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and verify_password(
            password,
            user.password_hash
        ):

            session["user_id"] = user.id

            session["username"] = user.username

            return redirect(
                url_for("auth.dashboard")
            )

    return render_template(
        "login.html"
    )


@auth_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "dashboard.html"
    )