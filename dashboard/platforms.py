from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Platform
from . import dashboard_bp

@dashboard_bp.route("/platforms")
def platforms():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    platforms = Platform.query.order_by(Platform.id.desc()).all()
    return render_template("dashboard/platforms.html", platforms=platforms)

@dashboard_bp.route("/platforms/create", methods=["POST"])
def create_platform():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    name = request.form.get("name")
    title = request.form.get("title")
    if Platform.query.filter_by(name=name).first():
        flash("این نام پلتفرم قبلاً وجود دارد!", "danger")
        return redirect(url_for("dashboard.platforms"))
    platform = Platform(name=name, title=title, is_active=True)
    db.session.add(platform)
    db.session.commit()
    flash("پلتفرم با موفقیت ایجاد شد.", "success")
    return redirect(url_for("dashboard.platforms"))

@dashboard_bp.route("/platforms/toggle/<int:platform_id>")
def toggle_platform(platform_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    platform = Platform.query.get(platform_id)
    if platform:
        platform.is_active = not platform.is_active
        db.session.commit()
        flash("وضعیت پلتفرم تغییر کرد.", "success")
    return redirect(url_for("dashboard.platforms"))

@dashboard_bp.route("/platforms/delete/<int:platform_id>")
def delete_platform(platform_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    platform = Platform.query.get(platform_id)
    if platform:
        db.session.delete(platform)
        db.session.commit()
        flash("پلتفرم حذف شد.", "success")
    return redirect(url_for("dashboard.platforms"))
