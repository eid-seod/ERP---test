from flask import Blueprint, jsonify, request, session
from sqlalchemy import select

from database import get_session
from models.client import Client
from models.invoice import Invoice
from routes.auth import current_user

bp = Blueprint("clients", __name__)


def _data(): return request.get_json(silent=True) or request.form.to_dict()


def _check_csrf(): return request.headers.get("X-CSRF-Token") == session.get("csrf_token")


def _allowed(client, user): return user and (user.role == "admin" or any(i.user_id == user.id for i in client.invoices))

@bp.get("/clients")
def list_clients():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    with get_session() as db:
        clients = db.scalars(select(Client).order_by(Client.name)).all()
        return jsonify({"clients": [c.to_dict() for c in clients]})

@bp.post("/clients")
def create_client():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _check_csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    data = _data()
    if not data.get("name", "").strip(): return jsonify({"error": "Client name is required."}), 400
    with get_session() as db:
        client = Client(name=data["name"].strip(), email=data.get("email", "").strip(), phone=data.get("phone", "").strip(), address=data.get("address", "").strip())
        db.add(client); db.commit(); return jsonify({"client": client.to_dict()}), 201

@bp.patch("/clients/<int:client_id>")
def update_client(client_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _check_csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    with get_session() as db:
        client = db.get(Client, client_id)
        if not client: return jsonify({"error": "Client not found."}), 404
        if not _allowed(client, user): return jsonify({"error": "Not authorized."}), 403
        data = _data()
        for field in ("name", "email", "phone", "address"):
            if field in data: setattr(client, field, data[field].strip())
        if not client.name: return jsonify({"error": "Client name is required."}), 400
        db.commit(); return jsonify({"client": client.to_dict()})

@bp.delete("/clients/<int:client_id>")
def delete_client(client_id):
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    if not _check_csrf(): return jsonify({"error": "Invalid CSRF token."}), 400
    with get_session() as db:
        client = db.get(Client, client_id)
        if not client: return jsonify({"error": "Client not found."}), 404
        if user.role != "admin": return jsonify({"error": "Admin access required."}), 403
        db.delete(client); db.commit(); return jsonify({"message": "Client deleted."})
