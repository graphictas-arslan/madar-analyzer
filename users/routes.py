from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for

from models.user import User


users_bp = Blueprint(
    "users",
    __name__
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
