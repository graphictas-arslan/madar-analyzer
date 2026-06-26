from . import dashboard_bp

from flask import render_template, redirect, url_for, session, request, flash, Response
from extensions import db
from models import Organization, Channel, Platform, Post, Bot, InstagramPage, InstagramPost, User
from sqlalchemy import func
from datetime import datetime
import requests
import io

from .excel_exporter import generate_excel

# ============== صفحه اصلی ==============
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
    for org in orgs:
        org.channel_count = Channel.query.filter_by(organization_id=org.id).count()
        channels = Channel.query.filter_by(organization_id=org.id).all()
        channel_ids = [c.id for c in channels]
        avg = db.session.query(func.avg(Post.score)).filter(
            Post.channel_id.in_(channel_ids),
            Post.score.isnot(None)
        ).scalar()
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

@dashboard_bp.route("/organizations/<int:org_id>/channels")
def organization_channels(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    organization = Organization.query.get(org_id)
    if not organization:
        flash("سازمان پیدا نشد!", "danger")
        return redirect(url_for("dashboard.organizations"))
    channels = Channel.query.filter_by(organization_id=org_id).order_by(Channel.id.desc()).all()
    for channel in channels:
        channel.post_count = Post.query.filter_by(channel_id=channel.id).count()
        avg = db.session.query(func.avg(Post.score)).filter(
            Post.channel_id == channel.id,
            Post.score.isnot(None)
        ).scalar()
        channel.avg_score = round(avg, 2) if avg else 0
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

# ============== پست‌های یک کانال ==============
@dashboard_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    query = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc())
    
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    
    posts = query.all()
    
    total_posts = len(posts)
    scored_posts = [p for p in posts if p.score is not None]
    avg_score = round(sum(p.score for p in scored_posts) / len(scored_posts), 2) if scored_posts else 0
    max_score = max(p.score for p in scored_posts) if scored_posts else 0
    min_score = min(p.score for p in scored_posts) if scored_posts else 0
    stats = {'total': total_posts, 'avg': avg_score, 'max': max_score, 'min': min_score}
    
    post_types = db.session.query(Post.post_type).filter_by(channel_id=channel_id).distinct().all()
    statuses = db.session.query(Post.status).filter_by(channel_id=channel_id).distinct().all()
    
    return render_template(
        "dashboard/channel_posts.html",
        channel=channel,
        posts=posts,
        stats=stats,
        now=datetime.utcnow,
        post_types=[t[0] for t in post_types],
        statuses=[s[0] for s in statuses],
        type_filter=type_filter,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to
    )

@dashboard_bp.route("/channels/<int:channel_id>/posts/export")
def export_channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    query = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc())
    
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    
    posts = query.all()
    
    excel_file = generate_excel(posts, title=f"Posts of {channel.channel_name}")
    safe_filename = f"posts_channel_{channel.id}.xlsx"
    
    return Response(
        excel_file.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )

# ============== لیست کل پست‌ها ==============
@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel_filter = request.args.get("channel", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    query = Post.query.join(Channel).order_by(Post.id.desc())
    if channel_filter:
        query = query.filter(Channel.channel_name.contains(channel_filter))
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    posts = query.all()
    channels = Channel.query.all()
    post_types = db.session.query(Post.post_type).distinct().all()
    statuses = db.session.query(Post.status).distinct().all()
    return render_template(
        "dashboard/posts.html",
        posts=posts,
        channels=channels,
        post_types=[t[0] for t in post_types],
        statuses=[s[0] for s in statuses],
        channel_filter=channel_filter,
        type_filter=type_filter,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to
    )

@dashboard_bp.route("/posts/export")
def export_posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel_filter = request.args.get("channel", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    query = Post.query.join(Channel).order_by(Post.id.desc())
    if channel_filter:
        query = query.filter(Channel.channel_name.contains(channel_filter))
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    posts = query.all()
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

# ============== مدیریت کاربران ==============
@dashboard_bp.route("/users")
def users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("dashboard.dashboard"))
    users = User.query.order_by(User.id.desc()).all()
    return render_template("dashboard/users.html", users=users)

@dashboard_bp.route("/users/create", methods=["GET", "POST"])
def create_user():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("dashboard.dashboard"))
    
    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        role = request.form.get("role")
        channel_ids = request.form.getlist("channels")
        
        new_user = User(
            full_name=full_name,
            username=username,
            mobile=mobile,
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        if role == "channel_admin" and channel_ids:
            channels = Channel.query.filter(Channel.id.in_(channel_ids)).all()
            new_user.channels = channels
            db.session.commit()
        
        flash(f"کاربر {username} با نقش {role} ایجاد شد.", "success")
        return redirect(url_for("dashboard.users"))
    
    channels = Channel.query.all()
    return render_template(
        "dashboard/create_user.html",
        channels=channels,
        roles=["admin", "channel_admin", "manager"]
    )

@dashboard_bp.route("/users/delete/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("dashboard.dashboard"))
    target = User.query.get(user_id)
    if target:
        db.session.delete(target)
        db.session.commit()
        flash("کاربر حذف شد.", "success")
    return redirect(url_for("dashboard.users"))

@dashboard_bp.route("/users/toggle/<int:user_id>")
def toggle_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("شما دسترسی به این صفحه را ندارید.", "danger")
        return redirect(url_for("dashboard.dashboard"))
    target = User.query.get(user_id)
    if target:
        target.is_active = not target.is_active
        db.session.commit()
        flash("وضعیت کاربر تغییر کرد.", "success")
    return redirect(url_for("dashboard.users"))

# ============== ادامه کدها (ربات‌ها، پلتفرم‌ها، اینستاگرام و ...) ==============
# ... (بقیه کدها مانند قبل)