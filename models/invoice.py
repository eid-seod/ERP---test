from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


MONEY = Decimal("0.01")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    client = relationship("Client", back_populates="invoices")
    user = relationship("User", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceItem.id")

    @property
    def subtotal(self):
        return sum((Decimal(str(item.quantity)) * Decimal(str(item.unit_price)) for item in self.items), Decimal("0")).quantize(MONEY, rounding=ROUND_HALF_UP)

    @property
    def tax_amount(self):
        return (self.subtotal * Decimal(str(self.tax_rate)) / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    def to_dict(self, include_items=True):
        data = {"id": self.id, "invoice_number": self.invoice_number, "client_id": self.client_id,
                "client_name": self.client.name if self.client else "", "user_id": self.user_id,
                "issue_date": self.issue_date.isoformat() if self.issue_date else None,
                "due_date": self.due_date.isoformat() if self.due_date else None, "status": self.status,
                "tax_rate": float(self.tax_rate or 0), "subtotal": float(self.subtotal),
                "tax_amount": float(self.tax_amount), "total": float(self.total), "notes": self.notes}
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")

    @property
    def amount(self):
        return (Decimal(str(self.quantity)) * Decimal(str(self.unit_price))).quantize(MONEY, rounding=ROUND_HALF_UP)

    def to_dict(self):
        return {"id": self.id, "description": self.description, "quantity": float(self.quantity),
                "unit_price": float(self.unit_price), "amount": float(self.amount)}
