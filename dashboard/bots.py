from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Post
from sqlalchemy import func
from .core import dashboard_bp  # این خط مهم است

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
