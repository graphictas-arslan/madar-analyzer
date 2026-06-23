from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from extensions import db
from models import User, Channel, Post, Platform
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            session["user_id"] = user.id
            flash("خوش آمدید!", "success")
            return redirect(url_for("dashboard.dashboard"))
        flash("نام کاربری یا رمز عبور اشتباه است", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))

@auth_bp.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    message = update.get("message")
    if not message:
        return jsonify({"status": "ignored"})

    chat = message.get("chat", {})
    # پیدا کردن پلتفرم بله
    platform = Platform.query.filter_by(name="bale").first()
    if not platform:
        platform = Platform(name="bale", title="Bale")
        db.session.add(platform)
        db.session.commit()

    channel = Channel.query.filter_by(
        platform_id=platform.id,
        bale_channel_id=str(chat.get("id"))
    ).first()

    if not channel:
        channel = Channel(
            platform_id=platform.id,
            bale_channel_id=str(chat.get("id")),
            channel_name=chat.get("title", "Unknown"),
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
            author_name=message.get("from", {}).get("username"),
            content_type=content_type,
            text=message.get("text"),
            caption=message.get("caption"),
            publish_time=datetime.utcfromtimestamp(message.get("date")),
            status="pending"
        )
        db.session.add(post)
        db.session.commit()

    return jsonify({"status": "saved"})
