from flask import Blueprint
from flask import request
from flask import jsonify

from extensions import db
from models.channel import Channel
from models.post import Post


bot_bp = Blueprint(
    "bot",
    __name__
)


@bot_bp.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json()

    message = update.get("message")

    if not message:
        return jsonify({"status": "ignored"})

    chat = message.get("chat", {})

    channel = Channel.query.filter_by(
        bale_channel_id=str(chat.get("id"))
    ).first()

    if not channel:

        channel = Channel(
            bale_channel_id=str(chat.get("id")),
            channel_name=chat.get("title"),
            username=chat.get("username"),
            status="active"
        )

        db.session.add(channel)
        db.session.commit()

    content_type = "text"

    if "video" in message:
        content_type = "video"

    elif "photo" in message:
        content_type = "photo"

    elif "document" in message:
        content_type = "document"

    post = Post.query.filter_by(
        bale_post_id=str(message.get("message_id"))
    ).first()

    if not post:

        post = Post(
            channel_id=channel.id,
            bale_post_id=str(message.get("message_id")),
            author_name=None,
            content_type=content_type,
            text=message.get("text"),
            caption=message.get("caption"),
            publish_time=None,
            status="active"
        )

        db.session.add(post)
        db.session.commit()

    return jsonify(
        {
            "status": "saved"
        }
    )
