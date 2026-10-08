"""Platform-side ORM models for company registration metadata.

These models deliberately contain no relationships to invoices or clients.  Company
financial data belongs exclusively to the separate SQLite database represented by
``db_filename``.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    company_type: Mapped[str] = mapped_column(String(30), nullable=False)
    legal_form: Mapped[str] = mapped_column(String(40), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="provisioning")
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    db_filename: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class CompanyMembership(Base):
    __tablename__ = "company_memberships"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="owner")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


Index("ix_companies_status", Company.status)
Index("ix_companies_company_type", Company.company_type)
Index("ix_company_memberships_company_id", CompanyMembership.company_id)
Index("ix_company_memberships_user_status", CompanyMembership.user_id, CompanyMembership.status)

__all__ = ["Company", "CompanyMembership", "utcnow"]
