from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Post
from sqlalchemy import func
from .core import dashboard_bp  # این خط مهم است

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
    return redirect(url_for("dashboard.channel_posts", channel_id=post.channel_id))
