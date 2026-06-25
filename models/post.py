from extensions import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False, index=True)
    platform_post_id = db.Column(db.String(200), nullable=False)  # تغییر نام
    author_name = db.Column(db.String(200))
    post_type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text)
    caption = db.Column(db.Text)
    media_url = db.Column(db.Text)
    thumbnail_url = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0)
    ai_score = db.Column(db.Float, default=0)
    publish_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Post {self.platform_post_id}>"
