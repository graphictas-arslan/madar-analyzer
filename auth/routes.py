from flask import Blueprint
from flask import render_template


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login")
def login():

    return render_template(
        "login.html"
    )

from models.user import User
from extensions import db
from auth.utils import hash_password


@auth_bp.route("/create-admin")
def create_admin():

    admin = User.query.filter_by(
        username="admin"
    ).first()

    if admin:
        return "Admin already exists"

    admin = User(
        full_name="System Admin",
        username="admin",
        password_hash=hash_password(
            "Admin123tas"
        ),
        is_super_admin=True,
        is_active=True
    )

    db.session.add(admin)
    db.session.commit()

    return "Admin created successfully"