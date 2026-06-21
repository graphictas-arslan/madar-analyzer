from extensions import db
from datetime import datetime


class Channel(db.Model):

    __tablename__ = "channels"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    platform_id = db.Column(
        db.Integer,
        db.ForeignKey("platforms.id"),
        nullable=False,
        index=True
    )

    channel_id = db.Column(
        db.String(150),
        nullable=False
    )

    username = db.Column(
        db.String(150)
    )

    title = db.Column(
        db.String(250),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    monitoring_enabled = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "platform_id",
            "channel_id",
            name="uq_platform_channel"
        ),
    )

    def __repr__(self):
        return f"<Channel {self.title}>"
