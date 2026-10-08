from datetime import datetime, timezone
import json

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserAuditEvent(Base):
    __tablename__ = 'user_audit_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    actor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    before_data: Mapped[str] = mapped_column(Text, nullable=False)
    after_data: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'actor_id': self.actor_id, 'target_id': self.target_id,
                'actor_name': self.actor_name, 'actor_email': self.actor_email, 'action': self.action,
                'before': json.loads(self.before_data), 'after': json.loads(self.after_data),
                'timestamp': self.changed_at.isoformat() + 'Z', 'ip_address': self.ip_address}


class PlatformSetting(Base):
    __tablename__ = 'platform_settings'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    integer_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
