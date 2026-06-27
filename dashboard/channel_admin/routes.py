from flask import Blueprint, render_template, redirect, url_for, session, flash, request, Response
from extensions import db
from models import User, Channel, Post
from datetime import datetime
from sqlalchemy import func
import io
import csv

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
    
    # آمار
    total_channels = len(channels)
    total_posts = Post.query.filter(Post.channel_id.in_([c.id for c in channels])).count()
    scored_posts = Post.query.filter(Post.channel_id.in_([c.id for c in channels]), Post.score.isnot(None)).count()
    
    # میانگین امتیاز کانال‌ها
    avg_score = db.session.query(func.avg(Post.score)).filter(
        Post.channel_id.in_([c.id for c in channels]),
        Post.score.isnot(None)
    ).scalar() or 0
    
    return render_template(
        "channel_admin/index.html",
        channels=channels,
        total_channels=total_channels,
        total_posts=total_posts,
        scored_posts=scored_posts,
        avg_score=round(avg_score, 2)
    )

@channel_admin_bp.route("/channels")
def channels():
    user = User.query.get(session["user_id"])
    channels = Channel.query.filter(Channel.id.in_([c.id for c in user.channels])).all()
    return render_template("channel_admin/channels.html", channels=channels)

@channel_admin_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    user = User.query.get(session["user_id"])
    if channel_id not in [c.id for c in user.channels]:
        flash("شما دسترسی به این کانال را ندارید.", "danger")
        return redirect(url_for("channel_admin.dashboard"))
    
    channel = Channel.query.get(channel_id)
    posts = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc()).all()
    
    # آمار کانال
    total_posts = len(posts)
    scored_posts = [p for p in posts if p.score is not None]
    avg_score = round(sum(p.score for p in scored_posts) / len(scored_posts), 2) if scored_posts else 0
    
    return render_template(
        "channel_admin/posts.html",
        channel=channel,
        posts=posts,
        total_posts=total_posts,
        avg_score=avg_score
    )

@channel_admin_bp.route("/channels/<int:channel_id>/posts/export")
def export_channel_posts(channel_id):
    user = User.query.get(session["user_id"])
    if channel_id not in [c.id for c in user.channels]:
        flash("شما دسترسی به این کانال را ندارید.", "danger")
        return redirect(url_for("channel_admin.dashboard"))
    
    channel = Channel.query.get(channel_id)
    posts = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc()).all()
    
    # ایجاد فایل CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['شناسه', 'نوع', 'متن', 'کپشن', 'تاریخ', 'امتیاز'])
    for post in posts:
        writer.writerow([
            post.id,
            post.post_type,
            post.text or '',
            post.caption or '',
            post.publish_date.strftime('%Y-%m-%d') if post.publish_date else '',
            post.score or 0
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=posts_{channel.channel_name}.csv"
        }
    )
