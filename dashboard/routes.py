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
    # ============== مدیریت ربات‌ها ==============
from models import Bot
import requests

@dashboard_bp.route("/bots")
def bots():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    bots = Bot.query.order_by(Bot.id.desc()).all()
    return render_template("dashboard/bots.html", bots=bots)

@dashboard_bp.route("/bots/create", methods=["POST"])
def create_bot():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    name = request.form.get("name")
    token = request.form.get("token")
    
    if Bot.query.filter_by(token=token).first():
        flash("این توکن قبلاً ثبت شده!", "danger")
        return redirect(url_for("dashboard.bots"))
    
    bot = Bot(name=name, token=token)
    db.session.add(bot)
    db.session.commit()
    flash("ربات با موفقیت ثبت شد.", "success")
    return redirect(url_for("dashboard.bots"))

@dashboard_bp.route("/bots/toggle/<int:bot_id>")
def toggle_bot(bot_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    bot = Bot.query.get(bot_id)
    if bot:
        bot.is_active = not bot.is_active
        db.session.commit()
        flash("وضعیت ربات تغییر کرد.", "success")
    return redirect(url_for("dashboard.bots"))

@dashboard_bp.route("/bots/delete/<int:bot_id>")
def delete_bot(bot_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    bot = Bot.query.get(bot_id)
    if bot:
        db.session.delete(bot)
        db.session.commit()
        flash("ربات حذف شد.", "success")
    return redirect(url_for("dashboard.bots"))
#<--!ست وبهوک-->
@dashboard_bp.route("/bots/set-webhook/<int:bot_id>")
def set_webhook(bot_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    bot = Bot.query.get(bot_id)
    if not bot:
        flash("ربات پیدا نشد!", "danger")
        return redirect(url_for("dashboard.bots"))
    
    webhook_url = request.host_url.rstrip('/') + "/auth/webhook"
    
    # تشخیص پلتفرم
    if bot.platform == "telegram":
        api_url = f"https://api.telegram.org/bot{bot.token}/setWebhook"
    elif bot.platform == "bale":
        api_url = f"https://api.bale.ai/bot{bot.token}/setWebhook"
    else:
        flash("پلتفرم نامعتبر است!", "danger")
        return redirect(url_for("dashboard.bots"))
    
    try:
        response = requests.post(api_url, data={"url": webhook_url}, timeout=10)
        result = response.json()
        if result.get("ok"):
            bot.webhook_url = webhook_url
            bot.last_webhook_set = datetime.utcnow()
            db.session.commit()
            flash(f"وب‌هوک برای {bot.platform} با موفقیت تنظیم شد.", "success")
        else:
            flash(f"خطا در تنظیم وب‌هوک: {result.get('description')}", "danger")
    except Exception as e:
        flash(f"خطا در اتصال به سرور {bot.platform}: {str(e)}", "danger")
    
    return redirect(url_for("dashboard.bots"))

    # ============== پلتفرم‌ها ==============
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
    # ============== اینستاگرام ==============
from models import InstagramPage, InstagramPost
import requests
import json

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
    
    # دریافت اطلاعات پیج از API اینستاگرام
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
        # دریافت آخرین پست‌ها
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
