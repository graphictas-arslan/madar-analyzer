from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Post
from sqlalchemy import func
from .core import dashboard_bp  # این خط مهم است

@dashboard_bp.route("/channels")
def channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channels = Channel.query.order_by(Channel.id.desc()).all()
    organizations = Organization.query.all()
    platforms = Platform.query.all()
    return render_template(
        "dashboard/channels.html",
        channels=channels,
        organizations=organizations,
        platforms=platforms
    )

@dashboard_bp.route("/channels/create", methods=["POST"])
def create_channel():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel_name = request.form.get("channel_name")
    channel_id = request.form.get("channel_id")
    organization_id = request.form.get("organization_id")
    platform_id = request.form.get("platform_id")
    if Channel.query.filter_by(channel_id=channel_id).first():
        flash("این شناسه کانال قبلاً ثبت شده است!", "danger")
        return redirect(url_for("dashboard.channels"))
    channel = Channel(
        channel_name=channel_name,
        channel_id=channel_id,
        organization_id=organization_id,
        platform_id=platform_id,
        is_active=True
    )
    db.session.add(channel)
    db.session.commit()
    flash("کانال با موفقیت ایجاد شد.", "success")
    return redirect(url_for("dashboard.channels"))

@dashboard_bp.route("/channels/toggle/<int:channel_id>")
def toggle_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if channel:
        channel.is_active = not channel.is_active
        db.session.commit()
        flash("وضعیت کانال تغییر کرد.", "success")
    return redirect(url_for("dashboard.channels"))

@dashboard_bp.route("/channels/delete/<int:channel_id>")
def delete_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if channel:
        db.session.delete(channel)
        db.session.commit()
        flash("کانال حذف شد.", "success")
    return redirect(url_for("dashboard.channels"))

@dashboard_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    posts = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc()).all()
    total_posts = len(posts)
    scored_posts = [p for p in posts if p.score is not None]
    avg_score = round(sum(p.score for p in scored_posts) / len(scored_posts), 2) if scored_posts else 0
    max_score = max(p.score for p in scored_posts) if scored_posts else 0
    min_score = min(p.score for p in scored_posts) if scored_posts else 0
    stats = {
        'total': total_posts,
        'avg': avg_score,
        'max': max_score,
        'min': min_score
    }
    return render_template(
        "dashboard/channel_posts.html",
        channel=channel,
        posts=posts,
        stats=stats
    )
