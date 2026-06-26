from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from extensions import db
from models import User, Channel, Post, Platform
from datetime import datetime
import requests
from config import Config

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            session["user_id"] = user.id
            flash("خوش آمدید!", "success")
            
            # هدایت بر اساس نقش کاربر
            if user.role == "admin":
                return redirect(url_for("dashboard.dashboard"))
            elif user.role == "channel_admin":
                return redirect(url_for("channel_admin.dashboard"))
            elif user.role == "manager":
                return redirect(url_for("manager.dashboard"))
            else:
                return redirect(url_for("dashboard.dashboard"))  # پیش‌فرض
        
        flash("نام کاربری یا رمز عبور اشتباه است", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))

# ============== دریافت لینک دانلود فایل از بله ==============
def get_file_url(file_id, bot_token):
    """دریافت لینک دانلود فایل از بله"""
    try:
        url = f"https://tapi.bale.ai/bot{bot_token}/getFile"
        response = requests.post(url, data={"file_id": file_id})
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                file_path = data["result"]["file_path"]
                return f"https://tapi.bale.ai/file/bot{bot_token}/{file_path}"
    except Exception as e:
        print(f"❌ خطا در دریافت لینک فایل: {str(e)}")
    return None

# ============== وب‌هوک ==============
@auth_bp.route("/webhook", methods=["POST"])
def webhook():
    print("📩 وب‌هوک دریافت شد.")
    try:
        update = request.get_json()
        print(f"📦 داده‌های دریافتی: {update}")

        if not update or not update.get("message"):
            print("⚠️ پیام یافت نشد.")
            return jsonify({"status": "ignored"})

        message = update["message"]
        chat = message.get("chat", {})
        print(f"💬 چت: {chat}")

        # تشخیص پلتفرم از طریق هدر User-Agent
        user_agent = request.headers.get("User-Agent", "")
        if "TelegramBot" in user_agent:
            platform_name = "telegram"
        else:
            platform_name = "bale"
        print(f"📌 پلتفرم تشخیص داده شده: {platform_name}")

        platform = Platform.query.filter_by(name=platform_name).first()
        print(f"📌 پلتفرم: {platform}")

        if not platform:
            print(f"🆕 ایجاد پلتفرم {platform_name}...")
            platform = Platform(name=platform_name, title=platform_name.capitalize())
            db.session.add(platform)
            db.session.commit()
            print("✅ پلتفرم ایجاد شد.")

        # پیدا کردن کانال با channel_id
        channel = Channel.query.filter_by(
            platform_id=platform.id,
            channel_id=str(chat.get("id"))
        ).first()
        print(f"📢 کانال: {channel}")

        if not channel:
            print("🆕 ایجاد کانال جدید...")
            channel = Channel(
                platform_id=platform.id,
                channel_id=str(chat.get("id")),
                channel_name=chat.get("title", "Unknown"),
                username=chat.get("username"),
                status="active",
                organization_id=None
            )
            db.session.add(channel)
            db.session.commit()
            print("✅ کانال ایجاد شد (بدون سازمان).")

        content_type = "text"
        if "video" in message:
            content_type = "video"
        elif "photo" in message:
            content_type = "photo"
        elif "document" in message:
            content_type = "document"
        print(f"🖼️ نوع محتوا: {content_type}")

        # پیدا کردن پست
        post = Post.query.filter_by(
            platform_post_id=str(message.get("message_id"))
        ).first()
        print(f"📝 پست موجود: {post}")

        if not post:
            print("🆕 ایجاد پست جدید...")
            
            # دریافت لینک عکس یا ویدئو
            media_url = None
            thumbnail_url = None
            bot_token = Config.BALE_TOKEN
            
            if content_type == "photo":
                print("📸 پردازش عکس...")
                if "photo" in message:
                    photos = message["photo"]
                    if photos:
                        file_id = photos[-1]["file_id"]
                        print(f"📸 file_id یافت شد: {file_id}")
                        media_url = get_file_url(file_id, bot_token)
                        print(f"🔗 media_url: {media_url}")
                        thumbnail_url = media_url
                elif "document" in message and message["document"]["mime_type"].startswith("image/"):
                    file_id = message["document"]["file_id"]
                    print(f"📸 file_id یافت شد: {file_id}")
                    media_url = get_file_url(file_id, bot_token)
                    print(f"🔗 media_url: {media_url}")
                    thumbnail_url = media_url
            elif content_type == "video":
                print("🎬 پردازش ویدئو...")
                if "video" in message:
                    file_id = message["video"]["file_id"]
                    print(f"📸 file_id یافت شد: {file_id}")
                    media_url = get_file_url(file_id, bot_token)
                    print(f"🔗 media_url: {media_url}")
                    thumbnail_url = media_url
                elif "document" in message and message["document"]["mime_type"].startswith("video/"):
                    file_id = message["document"]["file_id"]
                    print(f"📸 file_id یافت شد: {file_id}")
                    media_url = get_file_url(file_id, bot_token)
                    print(f"🔗 media_url: {media_url}")
                    thumbnail_url = media_url

            post = Post(
                channel_id=channel.id,
                platform_post_id=str(message.get("message_id")),
                author_name=message.get("from", {}).get("username"),
                post_type=content_type,
                text=message.get("text"),
                caption=message.get("caption"),
                publish_date=datetime.utcfromtimestamp(message.get("date")),
                status="pending",
                media_url=media_url,
                thumbnail_url=thumbnail_url
            )
            db.session.add(post)
            db.session.commit()
            print("✅ پست ذخیره شد.")

        print("✅ وب‌هوک با موفقیت پردازش شد.")
        return jsonify({"status": "saved"})

    except Exception as e:
        print("❌ خطای وب‌هوک:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route("/setup", methods=["GET"])
def setup_admin():
    existing = User.query.filter_by(username="admin").first()
    if existing:
        return "کاربر admin از قبل وجود دارد! برو لاگین کن."
    
    user = User(
        username="admin",
        full_name="مدیر سیستم",
        mobile="09123456789",
        is_active=True,
        is_super_admin=True
    )
    user.set_password("123456")
    db.session.add(user)
    db.session.commit()
    
    return "✅ کاربر admin با موفقیت ساخته شد! حالا برو به صفحه لاگین و با رمز 123456 وارد شو."
