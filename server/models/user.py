from datetime import datetime

from sqlalchemy.orm import validates

from .extensions import bcrypt, db
from .mixins import SerializerMixin


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    notes = db.relationship(
        "Note",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @validates("username")
    def validate_username(self, _, username):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return username

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password):
        if not raw_password or len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def authenticate(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def public_dict(self):
        return {"id": self.id, "username": self.username}
