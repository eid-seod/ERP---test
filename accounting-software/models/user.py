from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    session_epoch: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    invoices = relationship("Invoice", back_populates="user")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role, "is_active": self.is_active}


Index('ux_users_email_normalized', func.lower(User.email), unique=True)
