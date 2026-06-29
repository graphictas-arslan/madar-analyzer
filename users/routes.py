from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import User
from werkzeug.security import check_password_hash

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/")
def users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    users = User.query.order_by(User.id.desc()).all()
    return render_template("users/index.html", users=users)

@users_bp.route("/create", methods=["GET", "POST"])
def create_user():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        user = User(
            full_name=request.form["full_name"],
            username=request.form["username"],
            mobile=request.form["mobile"],
            is_active=True
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        flash("کاربر با موفقیت ایجاد شد.", "success")
        return redirect(url_for("users.users"))

    return render_template("users/create.html")

@users_bp.route("/delete/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("کاربر حذف شد.", "success")
    return redirect(url_for("users.users"))

@users_bp.route("/toggle/<int:user_id>")
def toggle_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        flash("وضعیت کاربر تغییر کرد.", "success")
    return redirect(url_for("users.users"))

# ============== تغییر رمز عبور ==============
@users_bp.route("/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    if not user:
        flash("کاربر پیدا نشد!", "danger")
        return redirect(url_for("dashboard.dashboard"))
    
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    # بررسی رمز فعلی
    if not user.check_password(current_password):
        flash("رمز عبور فعلی اشتباه است!", "danger")
        return redirect(url_for("dashboard.profile"))
    
    # بررسی تطابق رمز جدید
    if new_password != confirm_password:
        flash("رمز عبور جدید و تکرار آن مطابقت ندارند!", "danger")
        return redirect(url_for("dashboard.profile"))
    
    # بررسی طول رمز
    if len(new_password) < 6:
        flash("رمز عبور باید حداقل ۶ کاراکتر باشد!", "danger")
        return redirect(url_for("dashboard.profile"))
    
    # تغییر رمز
    user.set_password(new_password)
    db.session.commit()
    
    flash("✅ رمز عبور با موفقیت تغییر کرد!", "success")
    return redirect(url_for("dashboard.profile"))
