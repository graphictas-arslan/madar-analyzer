from . import dashboard_bp

from flask import render_template, redirect, url_for, session, request, flash, Response
from extensions import db
from models import Organization, Channel, Platform, Post, Bot, InstagramPage, InstagramPost
from sqlalchemy import func
from datetime import datetime
import requests
import io
import csv

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

# ============== پست‌های یک کانال (با فیلتر و خروجی اکسل) ==============
@dashboard_bp.route("/channels/<int:channel_id>/posts")
def channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    # دریافت پارامترهای فیلتر
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # ساخت کوئری پایه
    query = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc())
    
    # اعمال فیلترها
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    
    posts = query.all()
    
    # آمار
    total_posts = len(posts)
    scored_posts = [p for p in posts if p.score is not None]
    avg_score = round(sum(p.score for p in scored_posts) / len(scored_posts), 2) if scored_posts else 0
    max_score = max(p.score for p in scored_posts) if scored_posts else 0
    min_score = min(p.score for p in scored_posts) if scored_posts else 0
    stats = {'total': total_posts, 'avg': avg_score, 'max': max_score, 'min': min_score}
    
    # دریافت انواع و وضعیت‌ها برای فیلتر
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
    
    # دریافت پارامترهای فیلتر
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # ساخت کوئری پایه
    query = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc())
    
    # اعمال فیلترها
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    
    posts = query.all()
    
    # ایجاد فایل CSV در حافظه
    output = io.StringIO()
    writer = csv.writer(output)
    
    # هدرهای CSV
    writer.writerow([
        'شناسه', 'کانال', 'نوع', 'متن', 'کپشن', 
        'تاریخ انتشار', 'وضعیت', 'امتیاز', 
        'بازدید', 'لایک', 'کامنت'
    ])
    
    # نوشتن داده‌ها
    for post in posts:
        writer.writerow([
            post.id,
            post.channel.channel_name if post.channel else '-',
            post.post_type,
            post.text or '',
            post.caption or '',
            post.publish_date.strftime('%Y-%m-%d %H:%M') if post.publish_date else '',
            post.status,
            post.score or 0,
            post.views or 0,
            post.likes or 0,
            post.comments or 0
        ])
    
    # آماده‌سازی پاسخ
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=posts_{channel.channel_name}.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

# ============== لیست کل پست‌ها (با فیلتر و خروجی اکسل) ==============
@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    # دریافت پارامترهای فیلتر
    channel_filter = request.args.get("channel", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # ساخت کوئری پایه
    query = Post.query.join(Channel).order_by(Post.id.desc())
    
    # اعمال فیلترها
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
    
    # دریافت لیست کانال‌ها و انواع برای فیلتر
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
    
    # دریافت پارامترهای فیلتر
    channel_filter = request.args.get("channel", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # ساخت کوئری پایه
    query = Post.query.join(Channel).order_by(Post.id.desc())
    
    # اعمال فیلترها
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
    
    # ایجاد فایل CSV در حافظه
    output = io.StringIO()
    writer = csv.writer(output)
    
    # هدرهای CSV
    writer.writerow([
        'شناسه', 'کانال', 'نوع', 'متن', 'کپشن', 
        'تاریخ انتشار', 'وضعیت', 'امتیاز', 
        'بازدید', 'لایک', 'کامنت'
    ])
    
    # نوشتن داده‌ها
    for post in posts:
        writer.writerow([
            post.id,
            post.channel.channel_name if post.channel else '-',
            post.post_type,
            post.text or '',
            post.caption or '',
            post.publish_date.strftime('%Y-%m-%d %H:%M') if post.publish_date else '',
            post.status,
            post.score or 0,
            post.views or 0,
            post.likes or 0,
            post.comments or 0
        ])
    
    # آماده‌سازی پاسخ
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=posts_export.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
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

# ============== ربات‌ها ==============
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
    platform = request.form.get("platform")
    if Bot.query.filter_by(token=token).first():
        flash("این توکن قبلاً ثبت شده!", "danger")
        return redirect(url_for("dashboard.bots"))
    bot = Bot(name=name, token=token, platform=platform)
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

@dashboard_bp.route("/bots/set-webhook/<int:bot_id>")
def set_webhook(bot_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    bot = Bot.query.get(bot_id)
    if not bot:
        flash("ربات پیدا نشد!", "danger")
        return redirect(url_for("dashboard.bots"))
    host_url = request.host_url.rstrip('/')
    if host_url.startswith('http://'):
        host_url = host_url.replace('http://', 'https://')
    webhook_url = f"{host_url}/auth/webhook"
    if bot.platform == "telegram":
        api_url = f"https://api.telegram.org/bot{bot.token}/setWebhook"
    elif bot.platform == "bale":
        api_url = f"https://tapi.bale.ai/bot{bot.token}/setWebhook"
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

# ============== انتساب کانال ==============
@dashboard_bp.route("/channels/assign")
def assign_channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    unassigned_channels = Channel.query.filter_by(organization_id=None).all()
    organizations = Organization.query.all()
    return render_template(
        "dashboard/assign_channels.html",
        unassigned_channels=unassigned_channels,
        organizations=organizations
    )

@dashboard_bp.route("/channels/assign/<int:channel_id>", methods=["POST"])
def assign_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.assign_channels"))
    organization_id = request.form.get("organization_id")
    if organization_id:
        channel.organization_id = organization_id
        db.session.commit()
        flash(f"کانال {channel.channel_name} به سازمان انتخاب شده متصل شد.", "success")
    else:
        flash("لطفاً یک سازمان انتخاب کنید.", "danger")
    return redirect(url_for("dashboard.assign_channels"))

# ============== مدیریت دیتابیس ==============
@dashboard_bp.route("/db-manage", methods=["GET", "POST"])
def db_manage():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_tables":
                db.create_all()
                message = "✅ جدول‌ها با موفقیت ایجاد شدند!"
            elif action == "fix_channels":
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_id') THEN
                                ALTER TABLE channels ADD COLUMN channel_id VARCHAR(150);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_name') THEN
                                ALTER TABLE channels ADD COLUMN channel_name VARCHAR(250);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='platform_id') THEN
                                ALTER TABLE channels ADD COLUMN platform_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='organization_id') THEN
                                ALTER TABLE channels ADD COLUMN organization_id INTEGER;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ فیلدهای جدول channels تعمیر شدند!"
            elif action == "fix_posts":
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='channel_id') THEN
                                ALTER TABLE posts ADD COLUMN channel_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='platform_post_id') THEN
                                ALTER TABLE posts ADD COLUMN platform_post_id VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='post_type') THEN
                                ALTER TABLE posts ADD COLUMN post_type VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='author_name') THEN
                                ALTER TABLE posts ADD COLUMN author_name VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='publish_date') THEN
                                ALTER TABLE posts ADD COLUMN publish_date TIMESTAMP;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='status') THEN
                                ALTER TABLE posts ADD COLUMN status VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='score') THEN
                                ALTER TABLE posts ADD COLUMN score FLOAT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='caption') THEN
                                ALTER TABLE posts ADD COLUMN caption TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='text') THEN
                                ALTER TABLE posts ADD COLUMN text TEXT;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ فیلدهای جدول posts تعمیر شدند!"
            elif action == "fix_all":
                db.create_all()
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_id') THEN
                                ALTER TABLE channels ADD COLUMN channel_id VARCHAR(150);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_name') THEN
                                ALTER TABLE channels ADD COLUMN channel_name VARCHAR(250);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='platform_id') THEN
                                ALTER TABLE channels ADD COLUMN platform_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='organization_id') THEN
                                ALTER TABLE channels ADD COLUMN organization_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='channel_id') THEN
                                ALTER TABLE posts ADD COLUMN channel_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='platform_post_id') THEN
                                ALTER TABLE posts ADD COLUMN platform_post_id VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='post_type') THEN
                                ALTER TABLE posts ADD COLUMN post_type VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='author_name') THEN
                                ALTER TABLE posts ADD COLUMN author_name VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='publish_date') THEN
                                ALTER TABLE posts ADD COLUMN publish_date TIMESTAMP;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='status') THEN
                                ALTER TABLE posts ADD COLUMN status VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='score') THEN
                                ALTER TABLE posts ADD COLUMN score FLOAT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='caption') THEN
                                ALTER TABLE posts ADD COLUMN caption TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='text') THEN
                                ALTER TABLE posts ADD COLUMN text TEXT;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ همه فیلدها تعمیر شدند!"
            else:
                message = "⚠️ عملیات نامعتبر است."
        except Exception as e:
            message = f"❌ خطا: {str(e)}"
    return render_template("dashboard/db_manage.html", message=message)
# ============== کنسول (اجرای کد پایتون) ==============
@dashboard_bp.route("/console", methods=["GET", "POST"])
def console():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    output = None
    if request.method == "POST":
        code = request.form.get("code")
        try:
            # محیط امن برای اجرای کد
            local_ns = {
                'db': db,
                'models': __import__('models'),
                'requests': requests,
                'datetime': datetime
            }
            exec(code, {}, local_ns)
            output = "✅ کد با موفقیت اجرا شد!"
        except Exception as e:
            output = f"❌ خطا: {str(e)}"
    
    return render_template("dashboard/console.html", output=output)
    
