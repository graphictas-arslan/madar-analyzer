from flask import Blueprint
from flask import request
from flask import jsonify

bot_bp = Blueprint(
    "bot",
    __name__
)


@bot_bp.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json()

    print(update)

    return jsonify(
        {
            "status": "ok"
        }
    )
