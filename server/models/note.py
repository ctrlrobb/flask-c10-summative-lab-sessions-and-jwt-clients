from datetime import datetime

from sqlalchemy.orm import validates

from .extensions import db
from .mixins import SerializerMixin


class Note(db.Model, SerializerMixin):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="general")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="notes")

    @validates("title")
    def validate_title(self, _, title):
        title = (title or "").strip()
        if not title:
            raise ValueError("Title is required.")
        return title

    @validates("content")
    def validate_content(self, _, content):
        content = (content or "").strip()
        if not content:
            raise ValueError("Content is required.")
        return content

    @validates("category")
    def validate_category(self, _, category):
        category = (category or "general").strip()
        if not category:
            raise ValueError("Category is required.")
        return category
