from flask import Blueprint
from flask import render_template

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/channels/create")
def create_channel():

    return render_template(
        "create_channel.html"
    )
