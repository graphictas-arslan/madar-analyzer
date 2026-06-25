from flask import Flask, redirect, url_for, session
from config import Config
from database import init_database
from extensions import db, migrate
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from dashboard import dashboard_bp  # نه از dashboard.routes
import models

app = Flask(__name__)
app.config.from_object(Config)

# ثبت بلوپرینت‌ها
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(dashboard_bp)
app.register_blueprint(users_bp)

db.init_app(app)
migrate.init_app(app, db)

init_database(app)

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    # ساخت کاربر ادمین (فقط در زمان اجرای مستقیم)
    with app.app_context():
        from models import User
        from extensions import db
        existing = User.query.filter_by(username="admin").first()
        if not existing:
            admin = User(
                username="admin",
                full_name="مدیر سیستم",
                mobile="09123456789",
                is_active=True,
                is_super_admin=True
            )
            admin.set_password("123456")
            db.session.add(admin)
            db.session.commit()
            print("✅ کاربر admin با موفقیت ساخته شد!")
    
    app.run(host="0.0.0.0", port=8080)
