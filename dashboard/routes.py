from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Platform, Post
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# صفحه اصلی داشبورد
@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")

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

# ============== کانال‌ها ==============
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
    bale_channel_id = request.form.get("bale_channel_id")
    organization_id = request.form.get("organization_id")
    platform_id = request.form.get("platform_id")
    
    if Channel.query.filter_by(bale_channel_id=bale_channel_id).first():
        flash("این شناسه کانال قبلاً ثبت شده است!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    channel = Channel(
        channel_name=channel_name,
        bale_channel_id=bale_channel_id,
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

# ============== پست‌ها ==============
@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("dashboard/posts.html", posts=posts)

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
    
    return redirect(url_for("dashboard.posts"))

# ============== صفحه کانال با امتیاز ==============
@dashboard_bp.route("/channels/score/<int:channel_id>")
def channel_score(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    # محاسبه میانگین امتیازات پست‌های امتیازدار
    avg_score = db.session.query(func.avg(Post.score)).filter(
        Post.channel_id == channel_id,
        Post.score.isnot(None)
    ).scalar()
    
    channel.avg_score = round(avg_score, 2) if avg_score else 0
    
    return render_template(
        "dashboard/channel_score.html",
        channel=channel,
        posts=Post.query.filter_by(channel_id=channel_id).order_by(Post.id.desc()).all()
    )
