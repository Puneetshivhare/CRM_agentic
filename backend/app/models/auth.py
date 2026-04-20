"""
app/models/auth.py — SQLAlchemy model for auth_users table.

Design decision: auth_users has NO foreign keys to data tables.
This isolates auth so a data breach cannot cascade to credentials and vice versa.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.database import Base


class AuthUser(Base):
    """Stores user credentials. Isolated by design — no FKs to data tables."""

    __tablename__ = "auth_users"

    user_id: int = Column(Integer, primary_key=True, autoincrement=True)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    password_hash: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuthUser id={self.user_id} email={self.email!r}>"
