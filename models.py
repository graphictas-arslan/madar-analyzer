from database import db
from datetime import datetime


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True
    )

    password_hash = db.Column(
        db.String(255)
    )

    full_name = db.Column(
        db.String(100)
    )

    role = db.Column(
        db.String(50),
        default="channel_admin"
    )

    status = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



class Channel(db.Model):

    __tablename__ = "channels"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    bale_channel_id = db.Column(
        db.String(100),
        unique=True
    )

    channel_name = db.Column(
        db.String(200)
    )

    username = db.Column(
        db.String(100)
    )

    status = db.Column(
        db.String(50),
        default="pending"
    )

    monitoring_start = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



class Post(db.Model):

    __tablename__ = "posts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    channel_id = db.Column(
        db.Integer,
        db.ForeignKey("channels.id")
    )

    bale_post_id = db.Column(
        db.String(100)
    )

    author_name = db.Column(
        db.String(100)
    )

    content_type = db.Column(
        db.String(50)
    )

    text = db.Column(
        db.Text
    )

    caption = db.Column(
        db.Text
    )

    views = db.Column(
        db.Integer,
        default=0
    )

    score = db.Column(
        db.Integer
    )

    publish_time = db.Column(
        db.DateTime
    )

    status = db.Column(
        db.String(50),
        default="active"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
