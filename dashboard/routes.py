from . import dashboard_bp

from flask import render_template, redirect, url_for, session, request, flash, Response
from extensions import db
from models import Organization, Channel, Platform, Post, Bot, InstagramPage, InstagramPost, User
from sqlalchemy import func
from datetime import datetime
import requests
import io

from .excel_exporter import generate_excel

# ============== صفحه اصلی (داشبورد) ==============
@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    # آمارها
    total_posts = Post.query.count()
    total_channels = Channel.query.count()
    scored_posts = Post.query.filter(Post.score.isnot(None)).count()
    avg_score = db.session.query(func.avg(Post.score)).filter(Post.score.isnot(None)).scalar() or 0
    posts = Post.query.order_by(Post.publish_date.desc()).limit(10).all()
    
    return render_template(
        "dashboard/index.html",
        total_posts=total_posts,
        total_channels=total_channels,
        scored_posts=scored_posts,
        avg_score=round(avg_score, 1),
        posts=posts
    )

# ============== سازمان‌ها ==============
@dashboard_bp.route("/organizations")
def organizations():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    orgs = Organization.query.order_by(Organization.id.desc()).all()
    return render_template("dashboard/organizations.html", organizations=orgs)

@dashboard_bp.route("/organizations/create", methods=["POST"])
def create_organization():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    name = request.form.get("name")
    description = request.form.get("description")
    if Organization.query.filter_by(name=name).first():
        flash("این نام سازمان قبلاً وجود دارد!", "danger")
        return redirect(url_for("dashboard.organizations"))
    org = Organization(name=name, description=description)
    db.session.add(org)
    db.session.commit()
    flash("سازمان با موفقیت ایجاد شد.", "success")
    return redirect(url_for("dashboard.organizations"))

@dashboard_bp.route("/organizations/toggle/<int:org_id>")
def toggle_organization(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    org = Organization.query.get(org_id)
    if org:
        org.is_active = not org.is_active
        db.session.commit()
        flash("وضعیت سازمان تغییر کرد.", "success")
    return redirect(url_for("dashboard.organizations"))

@dashboard_bp.route("/organizations/delete/<int:org_id>")
def delete_organization(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    org = Organization.query.get(org_id)
    if org:
        db.session.delete(org)
        db.session.commit()
        flash("سازمان حذف شد.", "success")
    return redirect(url_for("dashboard.organizations"))

@dashboard_bp.route("/organizations/<int:org_id>/channels")
def organization_channels(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    organization = Organization.query.get(org_id)
    if not organization:
        flash("سازمان پیدا نشد!", "danger")
        return redirect(url_for("dashboard.organizations"))
    channels = Channel.query.filter_by(organization_id=org_id).order_by(Channel.id.desc()).all()
    return render_template(
        "dashboard/organization_channels.html",
        organization=organization,
        channels=channels
    )

# ============== کانال‌ها ==============
@dashboard_bp.route("/channels")
def channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channels = Channel.query.order_by(Channel.id.desc()).all()
    return render_template("dashboard/channels.html", channels=channels)

@dashboard_bp.route("/channels/create", methods=["POST"])
def create_channel():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel_name = request.form.get("channel_name")
    channel_id = request.form.get("channel_id")
    if Channel.query.filter_by(channel_id=channel_id).first():
        flash("این شناسه کانال قبلاً ثبت شده است!", "danger")
        return redirect(url_for("dashboard.channels"))
    channel = Channel(channel_name=channel_name, channel_id=channel_id, is_active=True)
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

# ============== پست‌ها ==============
@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    posts = Post.query.order_by(Post.publish_date.desc()).all()
    return render_template("dashboard/posts.html", posts=posts)

@dashboard_bp.route("/posts/export")
def export_posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    posts = Post.query.order_by(Post.publish_date.desc()).all()
    excel_file = generate_excel(posts)
    safe_filename = "posts_export.xlsx"
    return Response(
        excel_file.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )

# ============== امتیازدهی ==============
@dashboard_bp.route("/posts/score/<int:post_id>", methods=["POST"])
def score_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    post = Post.query.get(post_id)
    if not post:
        flash("پست پیدا نشد!", "danger")
        return redirect(url_for("dashboard.posts"))
    score = request.form.get("score")
    if score and score.isdigit():
        post.score = int(score)
        db.session.commit()
        flash(f"امتیاز {score} برای پست ثبت شد.", "success")
    else:
        flash("لطفاً یک عدد معتبر وارد کنید.", "danger")
    return redirect(url_for("dashboard.posts"))

# ============== کاربران ==============
@dashboard_bp.route("/users")
def users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    users = User.query.all()
    return render_template("dashboard/users.html", users=users)

# ============== تنظیمات ==============
@dashboard_bp.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/settings.html")
