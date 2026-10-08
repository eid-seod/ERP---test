import json
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

MONEY = Decimal("0.01")
ZERO = Decimal("0.00")


def dec(value):
    return Decimal(str(value or 0))


def quantize(value):
    return dec(value).quantize(MONEY, rounding=ROUND_HALF_UP)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=ZERO, nullable=False)  # legacy invoice-level rate
    tds_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tds_type: Mapped[str] = mapped_column(String(10), default="percent", nullable=False)
    tds_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=ZERO, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    client = relationship("Client", back_populates="invoices")
    user = relationship("User", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceItem.id")
    audit_entries = relationship("AuditTrail", back_populates="invoice", cascade="all, delete-orphan", order_by="AuditTrail.changed_at.desc()")

    @property
    def subtotal(self):
        return quantize(sum((dec(item.quantity) * dec(item.unit_price) for item in self.items), ZERO))

    @property
    def total_discount(self):
        return quantize(sum((dec(item.discount) for item in self.items), ZERO))

    @property
    def taxable_subtotal(self):
        return max(ZERO, quantize(self.subtotal - self.total_discount))

    @property
    def tax_amount(self):
        return quantize(sum((item.tax_amount for item in self.items), ZERO))

    @property
    def grand_total(self):
        return quantize(self.taxable_subtotal + self.tax_amount)

    @property
    def tds_amount(self):
        if not self.tds_enabled:
            return ZERO
        if self.tds_type == "fixed":
            return min(self.grand_total, quantize(self.tds_rate))
        return min(self.grand_total, quantize(self.grand_total * dec(self.tds_rate) / Decimal("100")))

    @property
    def net_payable(self):
        return max(ZERO, quantize(self.grand_total - self.tds_amount))

    @property
    def total(self):  # backwards-compatible alias
        return self.grand_total

    def snapshot(self):
        return {
            "client_id": self.client_id, "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None, "status": self.status,
            "currency": self.currency, "tds_enabled": self.tds_enabled, "tds_type": self.tds_type,
            "tds_rate": float(self.tds_rate or 0), "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
        }

    def to_dict(self, include_items=True):
        data = {"id": self.id, "invoice_number": self.invoice_number, "client_id": self.client_id,
                "client_name": self.client.name if self.client else "", "user_id": self.user_id,
                "issue_date": self.issue_date.isoformat() if self.issue_date else None,
                "due_date": self.due_date.isoformat() if self.due_date else None, "status": self.status,
                "currency": self.currency, "tax_rate": float(self.tax_rate or 0),
                "tds_enabled": self.tds_enabled, "tds_type": self.tds_type, "tds_rate": float(self.tds_rate or 0),
                "subtotal": float(self.subtotal), "total_discount": float(self.total_discount),
                "taxable_subtotal": float(self.taxable_subtotal), "tax_amount": float(self.tax_amount),
                "tds_amount": float(self.tds_amount), "grand_total": float(self.grand_total),
                "net_payable": float(self.net_payable), "total": float(self.grand_total), "notes": self.notes,
                "can_edit": self.status in {"draft", "open"}}
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    item_code: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=ZERO, nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=ZERO, nullable=False)

    invoice = relationship("Invoice", back_populates="items")

    @property
    def base_amount(self):
        return quantize(dec(self.quantity) * dec(self.unit_price))

    @property
    def taxable_amount(self):
        return max(ZERO, quantize(self.base_amount - dec(self.discount)))

    @property
    def tax_amount(self):
        return quantize(self.taxable_amount * dec(self.tax_rate) / Decimal("100"))

    @property
    def line_total(self):
        return quantize(self.taxable_amount + self.tax_amount)

    @property
    def amount(self):  # backwards-compatible alias
        return self.line_total

    def to_dict(self):
        return {"id": self.id, "item_code": self.item_code, "item_name": self.item_name,
                "description": self.description, "quantity": float(self.quantity), "unit_price": float(self.unit_price),
                "discount": float(self.discount), "tax_rate": float(self.tax_rate),
                "tax_amount": float(self.tax_amount), "line_total": float(self.line_total), "amount": float(self.line_total)}


class AuditTrail(Base):
    __tablename__ = "invoice_audit_trail"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    field_name: Mapped[str] = mapped_column(String(120), nullable=False)
    previous_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    new_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice = relationship("Invoice", back_populates="audit_entries")
    user = relationship("User")

    def to_dict(self):
        return {"id": self.id, "invoice_id": self.invoice_id, "user_id": self.user_id,
                "user_name": self.user.name if self.user else "", "action": self.action,
                "field_name": self.field_name, "previous_value": self.previous_value,
                "new_value": self.new_value, "changed_at": self.changed_at.isoformat()}
