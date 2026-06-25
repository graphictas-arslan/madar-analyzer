from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import InstagramPage, InstagramPost
from datetime import datetime
import requests
from . import dashboard_bp

@dashboard_bp.route("/instagram")
def instagram_pages():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    pages = InstagramPage.query.order_by(InstagramPage.id.desc()).all()
    return render_template("dashboard/instagram.html", pages=pages)

@dashboard_bp.route("/instagram/add", methods=["POST"])
def add_instagram_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    page_id = request.form.get("page_id")
    username = request.form.get("username")
    access_token = request.form.get("access_token")
    if InstagramPage.query.filter_by(page_id=page_id).first():
        flash("این پیج قبلاً ثبت شده!", "danger")
        return redirect(url_for("dashboard.instagram_pages"))
    try:
        url = f"https://graph.facebook.com/v22.0/{page_id}?fields=id,username,full_name,profile_picture_url,followers_count&access_token={access_token}"
        response = requests.get(url)
        data = response.json()
        page = InstagramPage(
            page_id=data.get("id"),
            username=data.get("username"),
            full_name=data.get("full_name"),
            profile_pic=data.get("profile_picture_url"),
            followers_count=data.get("followers_count", 0),
            access_token=access_token,
            is_active=True
        )
        db.session.add(page)
        db.session.commit()
        flash(f"پیج {page.username} با موفقیت اضافه شد.", "success")
    except Exception as e:
        flash(f"خطا در دریافت اطلاعات پیج: {str(e)}", "danger")
    return redirect(url_for("dashboard.instagram_pages"))

@dashboard_bp.route("/instagram/toggle/<int:page_id>")
def toggle_instagram_page(page_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    page = InstagramPage.query.get(page_id)
    if page:
        page.is_active = not page.is_active
        db.session.commit()
        flash("وضعیت پیج تغییر کرد.", "success")
    return redirect(url_for("dashboard.instagram_pages"))

@dashboard_bp.route("/instagram/delete/<int:page_id>")
def delete_instagram_page(page_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    page = InstagramPage.query.get(page_id)
    if page:
        db.session.delete(page)
        db.session.commit()
        flash("پیج حذف شد.", "success")
    return redirect(url_for("dashboard.instagram_pages"))

@dashboard_bp.route("/instagram/sync/<int:page_id>")
def sync_instagram_page(page_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    page = InstagramPage.query.get(page_id)
    if not page:
        flash("پیج پیدا نشد!", "danger")
        return redirect(url_for("dashboard.instagram_pages"))
    try:
        url = f"https://graph.facebook.com/v22.0/{page.page_id}/media?fields=id,media_type,media_url,thumbnail_url,caption,timestamp,like_count,comments_count,permalink&access_token={page.access_token}&limit=10"
        response = requests.get(url)
        data = response.json()
        for item in data.get("data", []):
            if not InstagramPost.query.filter_by(instagram_post_id=item["id"]).first():
                post = InstagramPost(
                    page_id=page.id,
                    instagram_post_id=item["id"],
                    media_type=item.get("media_type"),
                    media_url=item.get("media_url"),
                    thumbnail_url=item.get("thumbnail_url"),
                    caption=item.get("caption"),
                    permalink=item.get("permalink"),
                    timestamp=datetime.fromisoformat(item.get("timestamp").replace("Z", "+00:00")),
                    like_count=item.get("like_count", 0),
                    comments_count=item.get("comments_count", 0)
                )
                db.session.add(post)
        page.last_sync = datetime.utcnow()
        db.session.commit()
        flash("پست‌ها با موفقیت همگام‌سازی شدند.", "success")
    except Exception as e:
        flash(f"خطا در همگام‌سازی: {str(e)}", "danger")
    return redirect(url_for("dashboard.instagram_pages"))

@dashboard_bp.route("/instagram/posts/<int:page_id>")
def instagram_posts(page_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    page = InstagramPage.query.get(page_id)
    if not page:
        flash("پیج پیدا نشد!", "danger")
        return redirect(url_for("dashboard.instagram_pages"))
    posts = InstagramPost.query.filter_by(page_id=page_id).order_by(InstagramPost.timestamp.desc()).all()
    return render_template("dashboard/instagram_posts.html", page=page, posts=posts)

@dashboard_bp.route("/instagram/score/<int:post_id>", methods=["POST"])
def score_instagram_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    post = InstagramPost.query.get(post_id)
    if not post:
        flash("پست پیدا نشد!", "danger")
        return redirect(url_for("dashboard.instagram_pages"))
    score = request.form.get("score")
    if score and score.isdigit():
        post.score = int(score)
        post.status = "analyzed"
        db.session.commit()
        flash(f"امتیاز {score} برای پست ثبت شد.", "success")
    else:
        flash("لطفاً یک عدد معتبر وارد کنید.", "danger")
    return redirect(url_for("dashboard.instagram_posts", page_id=post.page_id))
