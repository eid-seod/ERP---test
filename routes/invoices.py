import json
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file, session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from sqlalchemy import func, select

from database import get_session
from models.client import Client
from models.invoice import AuditTrail, Invoice, InvoiceItem
from routes.auth import current_user

bp = Blueprint("invoices", __name__)
EDITABLE_STATUSES = {"draft", "open"}
LOCKED_STATUSES = {"approved", "posted", "fully_paid", "paid"}
VALID_STATUSES = EDITABLE_STATUSES | LOCKED_STATUSES | {"sent", "overdue", "cancelled"}
CURRENCIES = {"USD", "EUR", "GBP", "INR", "AED", "CAD", "AUD", "JPY"}


def _data(): return request.get_json(silent=True) or request.form.to_dict()

def _money(value, default=Decimal("0")):
    try:
        amount = Decimal(str(value))
        if amount < 0: return default
        return amount.quantize(Decimal("0.01"))
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

def _can_edit(invoice, user):
    return invoice.status in EDITABLE_STATUSES or user.role == "admin"

def _validate_items(items):
    clean = []
    errors = []
    for index, item in enumerate(items or [], start=1):
        item_code = str(item.get("item_code", "")).strip()
        item_name = str(item.get("item_name", "")).strip() or str(item.get("description", "")).strip()
        description = str(item.get("description", "")).strip() or item_name
        quantity = _money(item.get("quantity"), Decimal("-1")); unit_price = _money(item.get("unit_price"), Decimal("-1"))
        discount = _money(item.get("discount")); tax_rate = _money(item.get("tax_rate"))
        if not item_name: errors.append(f"Item {index}: item name is required.")
        if quantity <= 0: errors.append(f"Item {index}: quantity must be greater than zero.")
        if unit_price < 0: errors.append(f"Item {index}: unit price is invalid.")
        if discount > quantity * unit_price: errors.append(f"Item {index}: discount cannot exceed the line value.")
        if not errors[-1:] or not errors[-1].startswith(f"Item {index}:"):
            clean.append((item_code, item_name, description, quantity, unit_price, discount, tax_rate))
    return clean, errors

def _audit_changes(db, invoice, user_id, before, action="update"):
    after = invoice.snapshot()
    fields = set(before) | set(after)
    for field in sorted(fields):
        previous = json.dumps(before.get(field), sort_keys=True, default=str) if isinstance(before.get(field), (dict, list)) else str(before.get(field, ""))
        updated = json.dumps(after.get(field), sort_keys=True, default=str) if isinstance(after.get(field), (dict, list)) else str(after.get(field, ""))
        if previous != updated:
            db.add(AuditTrail(invoice_id=invoice.id, user_id=user_id, action=action, field_name=field, previous_value=previous, new_value=updated))

def _apply_payload(invoice, db, data, replace_items=True):
    errors = []
    if "client_id" in data:
        client = db.get(Client, data.get("client_id"))
        if not client: errors.append("A valid client is required.")
        else: invoice.client_id = client.id
    if "issue_date" in data:
        invoice.issue_date = _parse_date(data.get("issue_date")) or invoice.issue_date
    if "due_date" in data: invoice.due_date = _parse_date(data.get("due_date"))
    if "status" in data and data.get("status") in VALID_STATUSES: invoice.status = data["status"]
    if "currency" in data and str(data.get("currency")).upper() in CURRENCIES: invoice.currency = str(data["currency"]).upper()
    if "tds_enabled" in data: invoice.tds_enabled = bool(data.get("tds_enabled")) if isinstance(data.get("tds_enabled"), bool) else str(data.get("tds_enabled")).lower() in {"true", "1", "yes", "on"}
    if "tds_type" in data and data.get("tds_type") in {"percent", "fixed"}: invoice.tds_type = data["tds_type"]
    if "tds_rate" in data: invoice.tds_rate = _money(data.get("tds_rate"))
    if "notes" in data: invoice.notes = str(data.get("notes", "")).strip()
    if "items" in data and replace_items:
        raw_items = data.get("items")
        if raw_items and data.get("tax_rate") is not None:
            raw_items = [dict(item, tax_rate=item.get("tax_rate", data.get("tax_rate"))) for item in raw_items]
        items, item_errors = _validate_items(raw_items); errors.extend(item_errors)
        if not item_errors:
            invoice.items = [InvoiceItem(item_code=code, item_name=name, description=desc, quantity=qty, unit_price=price, discount=discount, tax_rate=tax) for code, name, desc, qty, price, discount, tax in items]
    return errors


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
        data = invoice.to_dict()
        data["audit"] = [entry.to_dict() for entry in invoice.audit_entries]
        return jsonify({"invoice": data})


@bp.get("/invoices/<int:invoice_id>/audit")
def invoice_audit(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        return jsonify({"audit": [entry.to_dict() for entry in invoice.audit_entries]})


@bp.get("/invoices/<int:invoice_id>/pdf")
def invoice_pdf(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
        styles = getSampleStyleSheet(); story = [Paragraph("<font color='#4263EB'><b>LEDGERLY</b></font>", styles["Title"]), Paragraph(f"INVOICE <b>{invoice.invoice_number}</b>", styles["Heading2"]), Spacer(1, 6 * mm)]
        story.append(Paragraph(f"<b>Bill to:</b> {invoice.client.name}<br/>{invoice.client.email or ''}<br/><br/><b>Issue date:</b> {invoice.issue_date} &nbsp;&nbsp; <b>Due:</b> {invoice.due_date or '—'} &nbsp;&nbsp; <b>Currency:</b> {invoice.currency}", styles["Normal"])); story.append(Spacer(1, 7 * mm))
        rows = [["Code", "Item", "Qty", "Unit price", "Discount", "Tax", "Line total"]] + [[item.item_code, item.item_name, f"{item.quantity:g}", f"{invoice.currency} {item.unit_price:,.2f}", f"{invoice.currency} {item.discount:,.2f}", f"{item.tax_rate:g}%", f"{invoice.currency} {item.line_total:,.2f}"] for item in invoice.items]
        table = Table(rows, repeatRows=1, colWidths=[22*mm, 48*mm, 15*mm, 25*mm, 25*mm, 18*mm, 28*mm]); table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#16233B")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#DCE2EC")), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 8), ("ALIGN", (2,1), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F7F8FB")]), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)])); story.append(table); story.append(Spacer(1, 7 * mm))
        summary = [["Subtotal", f"{invoice.currency} {invoice.subtotal:,.2f}"], ["Total discount", f"{invoice.currency} {invoice.total_discount:,.2f}"], ["Tax amount", f"{invoice.currency} {invoice.tax_amount:,.2f}"], ["Grand total", f"{invoice.currency} {invoice.grand_total:,.2f}"], ["TDS", f"- {invoice.currency} {invoice.tds_amount:,.2f}"], ["Net payable", f"{invoice.currency} {invoice.net_payable:,.2f}"]]; summary_table = Table(summary, colWidths=[45*mm, 45*mm], hAlign="RIGHT"); summary_table.setStyle(TableStyle([("ALIGN", (1,0), (-1,-1), "RIGHT"), ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"), ("LINEABOVE", (0,-1), (-1,-1), 1, colors.HexColor("#4263EB")), ("FONTSIZE", (0,0), (-1,-1), 10), ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)])); story.append(summary_table)
        if invoice.notes: story.extend([Spacer(1, 8 * mm), Paragraph(f"<b>Notes</b><br/>{invoice.notes}", styles["Normal"])])
        doc.build(story); buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{invoice.invoice_number}.pdf", mimetype="application/pdf")


@bp.post("/invoices")
def create_invoice():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    data = _data()
    with get_session() as db:
        invoice = Invoice(invoice_number=_next_number(db), user_id=user.id, client_id=0, currency="USD")
        errors = _apply_payload(invoice, db, data)
        if not invoice.client_id or not db.get(Client, invoice.client_id): errors.append("A valid client is required.")
        if not invoice.items: errors.append("Add at least one valid invoice item.")
        if errors: return jsonify({"errors": errors}), 400
        db.add(invoice); db.flush(); db.add(AuditTrail(invoice_id=invoice.id, user_id=user.id, action="create", field_name="invoice", previous_value="", new_value=json.dumps(invoice.snapshot(), sort_keys=True, default=str))); db.commit()
        return jsonify({"invoice": invoice.to_dict()}), 201


@bp.patch("/invoices/<int:invoice_id>")
def update_invoice(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    data = _data()
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        if not _can_edit(invoice, user): return jsonify({"error": f"Invoice status '{invoice.status}' is locked. Only Draft or Open invoices can be edited."}), 409
        before = invoice.snapshot(); errors = _apply_payload(invoice, db, data)
        if errors: return jsonify({"errors": errors}), 400
        _audit_changes(db, invoice, user.id, before); db.commit(); return jsonify({"invoice": invoice.to_dict(), "audit": [entry.to_dict() for entry in invoice.audit_entries]})


@bp.delete("/invoices/<int:invoice_id>")
def delete_invoice(invoice_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        invoice = _find_invoice(db, invoice_id, user)
        if not invoice: return jsonify({"error": "Invoice not found."}), 404
        if invoice.status not in EDITABLE_STATUSES and user.role != "admin": return jsonify({"error": "Locked invoices cannot be deleted."}), 409
        db.delete(invoice); db.commit(); return jsonify({"message": "Invoice deleted."})
