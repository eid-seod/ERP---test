from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, select

from database import get_session
from models.client import Client
from models.invoice import Invoice, InvoiceItem
from routes.auth import current_user

bp = Blueprint("invoices", __name__)


def _data(): return request.get_json(silent=True) or request.form.to_dict()
def _csrf(): return request.headers.get("X-CSRF-Token") == session.get("csrf_token")

def _money(value, default=Decimal("0")):
    try: return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError): return default

def _parse_date(value):
    if not value: return None
    try: return date.fromisoformat(value)
    except (ValueError, TypeError): return None

def _next_number(db):
    prefix = date.today().strftime("%Y%m")
    count = db.scalar(select(func.count(Invoice.id)).where(Invoice.invoice_number.like(f"INV-{prefix}-%"))) or 0
    return f"INV-{prefix}-{count + 1:04d}"

def _find_invoice(db, invoice_id, user):
    invoice = db.get(Invoice, invoice_id)
    return invoice if invoice and (user.role == "admin" or invoice.user_id == user.id) else None

def _validate_items(items):
    clean = []
    for item in items or []:
        description = str(item.get("description", "")).strip()
        quantity = _money(item.get("quantity"), Decimal("-1")); unit_price = _money(item.get("unit_price"), Decimal("-1"))
        if description and quantity > 0 and unit_price >= 0: clean.append((description, quantity, unit_price))
    return clean

@bp.get("/invoices")
def list_invoices():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        query = select(Invoice).order_by(Invoice.created_at.desc())
        if user.role != "admin": query = query.where(Invoice.user_id == user.id)
        return jsonify({"invoices": [i.to_dict(False) for i in db.scalars(query).all()]})

@bp.get("/invoices/<int:invoice_id>")
def get_invoice(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        return jsonify({"invoice": invoice.to_dict()})

@bp.post("/invoices")
def create_invoice():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    data = _data(); items = _validate_items(data.get("items", []))
    with get_session() as db:
        client = db.get(Client, data.get("client_id"))
        if not client: return jsonify({"error": "A valid client is required."}), 400
        if not items: return jsonify({"error": "Add at least one valid invoice item."}), 400
        invoice = Invoice(invoice_number=_next_number(db), client_id=client.id, user_id=user.id,
                          issue_date=_parse_date(data.get("issue_date")) or date.today(), due_date=_parse_date(data.get("due_date")),
                          status=data.get("status", "draft") if data.get("status") in {"draft", "sent", "paid", "overdue"} else "draft",
                          tax_rate=_money(data.get("tax_rate")), notes=str(data.get("notes", "")).strip())
        invoice.items = [InvoiceItem(description=d, quantity=q, unit_price=p) for d, q, p in items]
        db.add(invoice); db.commit(); return jsonify({"invoice": invoice.to_dict()}), 201

@bp.patch("/invoices/<int:invoice_id>")
def update_invoice(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    data = _data()
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        if "issue_date" in data: invoice.issue_date = _parse_date(data["issue_date"])
        if "due_date" in data: invoice.due_date = _parse_date(data["due_date"])
        if data.get("status") in {"draft", "sent", "paid", "overdue"}: invoice.status = data["status"]
        if "tax_rate" in data: invoice.tax_rate = _money(data["tax_rate"])
        if "notes" in data: invoice.notes = str(data["notes"]).strip()
        if "client_id" in data and db.get(Client, data["client_id"]): invoice.client_id = int(data["client_id"])
        if "items" in data:
            items = _validate_items(data["items"])
            if not items: return jsonify({"error": "Add at least one valid invoice item."}), 400
            invoice.items = [InvoiceItem(description=d, quantity=q, unit_price=p) for d, q, p in items]
        db.commit(); return jsonify({"invoice": invoice.to_dict()})

@bp.delete("/invoices/<int:invoice_id>")
def delete_invoice(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        db.delete(invoice); db.commit(); return jsonify({"message": "Invoice deleted."})
