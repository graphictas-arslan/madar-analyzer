from extensions import db
from datetime import datetime

class InstagramPage(db.Model):
    __tablename__ = "instagram_pages"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(100), unique=True, nullable=False)  # شناسه پیج در اینستاگرام
    username = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200))
    profile_pic = db.Column(db.String(500))
    followers_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    access_token = db.Column(db.String(500))  # توکن دسترسی (برای API)
    webhook_url = db.Column(db.String(500))
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InstagramPage {self.username}>"

class InstagramPost(db.Model):
    __tablename__ = "instagram_posts"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("instagram_pages.id"), nullable=False, index=True)
    instagram_post_id = db.Column(db.String(100), unique=True, nullable=False)  # شناسه پست در اینستاگرام
    media_type = db.Column(db.String(50))  # image, video, carousel, story
    media_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    caption = db.Column(db.Text)
    permalink = db.Column(db.String(500))  # لینک پست
    timestamp = db.Column(db.DateTime)  # زمان انتشار
    like_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)  # برای ویدئوها و استوری
    is_story = db.Column(db.Boolean, default=False)  # آیا استوری است؟
    score = db.Column(db.Float, default=0)  # امتیاز تحلیل
    status = db.Column(db.String(50), default="pending")  # pending, analyzed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    page = db.relationship("InstagramPage", backref="posts")

    def __repr__(self):
        return f"<InstagramPost {self.instagram_post_id}>"
