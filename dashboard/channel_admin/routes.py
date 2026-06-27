from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from extensions import db
from models import User, Channel, Post
from datetime import datetime

channel_admin_bp = Blueprint("channel_admin", __name__, url_prefix="/channel-admin")

@channel_admin_bp.before_request
def check_permission():
    """بررسی اینکه کاربر ادمین کانال است"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if not user or user.role != "channel_admin":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("auth.login"))

@channel_admin_bp.route("/")
def dashboard():
    user = User.query.get(session["user_id"])
    # فقط کانال‌هایی که به کاربر اختصاص داده شده
    channels = Channel.query.filter(Channel.id.in_([c.id for c in user.channels])).all()
    return render_template("channel_admin/index.html", channels=channels, user=user)

@channel_admin_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    user = User.query.get(session["user_id"])
    # بررسی دسترسی به کانال
    if channel_id not in [c.id for c in user.channels]:
        flash("شما دسترسی به این کانال را ندارید.", "danger")
        return redirect(url_for("channel_admin.dashboard"))
    
    channel = Channel.query.get(channel_id)
    posts = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc()).all()
    return render_template("channel_admin/posts.html", channel=channel, posts=posts)

@channel_admin_bp.route("/channels/<int:channel_id>/posts/export")
def export_channel_posts(channel_id):
    user = User.query.get(session["user_id"])
    if channel_id not in [c.id for c in user.channels]:
        flash("شما دسترسی به این کانال را ندارید.", "danger")
        return redirect(url_for("channel_admin.dashboard"))
    
    # ... کد خروجی اکسل از excel_exporter
    return redirect(url_for("channel_admin.channel_posts", channel_id=channel_id))
