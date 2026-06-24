from extensions import db
from datetime import datetime

class Bot(db.Model):
    __tablename__ = "bots"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)          # نام ربات
    token = db.Column(db.String(255), nullable=False)         # توکن بله
    platform = db.Column(db.String(50), default="bale")       # پلتفرم (بله، تلگرام و...)
    is_active = db.Column(db.Boolean, default=True)           # فعال/غیرفعال
    webhook_url = db.Column(db.String(255))                   # آدرس وب‌هوک تنظیم شده
    last_webhook_set = db.Column(db.DateTime)                 # آخرین زمان تنظیم وب‌هوک
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Bot {self.name}>"
