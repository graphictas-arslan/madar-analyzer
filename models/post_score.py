from extensions import db
from datetime import datetime


class PostScore(db.Model):

    __tablename__ = "post_scores"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("posts.id"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    score_type = db.Column(
        db.String(50),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<PostScore {self.score}>"
