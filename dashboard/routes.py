from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Platform, Post, Bot, InstagramPage, InstagramPost
from sqlalchemy import func
from datetime import datetime
import requests

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ============== صفحه اصلی داشبورد ==============
@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")


# ============== سازمان‌ها (سطح ۱ - کارتی) ==============
@dashboard_bp.route("/organizations")
def organizations():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    orgs = Organization.query.order_by(Organization.id.desc()).all()
    # محاسبه آمار هر سازمان
    for org in orgs:
        org.channel_count = Channel.query.filter_by(organization_id=org.id).count()
        # میانگین امتیاز کانال‌های این سازمان
        avg = db.session.query(func.avg(Channel.avg_score)).filter(Channel.organization_id==org.id).scalar()
        org.avg_score = round(avg, 2) if avg else 0
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


# ============== کانال‌های یک سازمان (سطح ۲ - کارتی) ==============
@dashboard_bp.route("/organizations/<int:org_id>/channels")
def organization_channels(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    organization = Organization.query.get(org_id)
    if not organization:
        flash("سازمان پیدا نشد!", "danger")
        return redirect(url_for("dashboard.organizations"))
    
    channels = Channel.query.filter_by(organization_id=org_id).order_by(Channel.id.desc()).all()
    # محاسبه آمار هر کانال
    for channel in channels:
        channel.post_count = Post.query.filter_by(channel_id=channel.id).count()
        # میانگین امتیاز پست‌های این کانال
        avg = db.session.query(func.avg(Post.score)).filter(Post.channel_id==channel.id, Post.score.isnot(None)).scalar()
        channel.avg_score = round(avg, 2) if avg else 0
    
    return render_template(
        "dashboard/organization_channels.html",
        organization=organization,
        channels=channels
    )


# ============== پست‌های یک کانال (سطح ۳ - گرید اینستاگرامی) ==============
@dashboard_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    posts = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc()).all()
    
    # آمار کانال
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


# ============== امتیازدهی به پست ==============
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
        post.status = "active"
        db.session.commit()
        flash(f"امتیاز {score} برای پست ثبت شد.", "success")
    else:
        flash("لطفاً یک عدد معتبر وارد کنید.", "danger")
    return redirect(url_for("dashboard.channel_posts", channel_id=post.channel_id))


# ============== سایر بخش‌ها (ربات‌ها، اینستاگرام و...) ==============
# ... (بقیه کدهای مربوط به ربات‌ها، پلتفرم‌ها و اینستاگرام که قبلاً داشتید)
