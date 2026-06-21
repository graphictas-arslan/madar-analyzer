from extensions import db
from datetime import datetime


class ActivityLog(db.Model):

    __tablename__ = "activity_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer
    )

    action = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    ip_address = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<ActivityLog {self.action}>"
