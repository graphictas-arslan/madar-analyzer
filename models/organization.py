from extensions import db
from datetime import datetime


class Organization(db.Model):

    __tablename__ = "organizations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text
    )

    is_active = db.Column(
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

    def __repr__(self):
        return f"<Organization {self.name}>"
