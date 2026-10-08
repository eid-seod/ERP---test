import hmac
import re
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from database import get_session
from models.user import User
from auth_throttle import check_attempt

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _payload():
    return request.get_json(silent=True) or request.form.to_dict()


def _validate_user(data, require_password=True):
    errors = []
    if not data.get("name", "").strip(): errors.append("Name is required.")
    email = data.get("email", "").strip().lower()
    if not EMAIL_RE.match(email): errors.append("A valid email is required.")
    if require_password and len(data.get("password", "")) < 8: errors.append("Password must be at least 8 characters.")
    return errors, email


def current_user():
    user_id = session.get("user_id")
    if not user_id: return None
    with get_session() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active or user.deleted_at or session.get("session_epoch", 0) != user.session_epoch:
            return None
        return user


@bp.post("/login")
def login():
    data = _payload()
    if not isinstance(data, dict) or not isinstance(data.get('email', ''), str) or not isinstance(data.get('password', ''), str):
        return jsonify({'error': 'Invalid login data.'}), 400
    email = data.get("email", "").strip().lower()
    limited = check_attempt('login', email)
    if limited is not None: return limited
    with get_session() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email, User.is_active.is_(True), User.deleted_at.is_(None)))
        if not user or not user.check_password(data.get("password", "")):
            return jsonify({"error": "Invalid email or password."}), 401
        from super_admin.service import record_login
        record_login(db, user, request.remote_addr)
        db.commit()
        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        session["session_epoch"] = user.session_epoch
        session["csrf_token"] = current_app.config["TOKEN_FACTORY"]()
        return jsonify({"user": user.to_dict(), "csrf_token": session["csrf_token"]})


@bp.route("/register", methods=["GET", "POST"])
def register():
    from super_admin.service import registration_enabled
    if not registration_enabled(): abort(404)
    token = session.get('csrf_token')
    if not isinstance(token, str) or not token:
        token = session['csrf_token'] = current_app.config['TOKEN_FACTORY']()
    if request.method == 'GET':
        return render_template('register.html', registration_csrf=token, registration_values={})
    if not request.is_json:
        supplied = request.form.get('csrf_token', '')
        if not token or not hmac.compare_digest(token, supplied): abort(400, description='Invalid CSRF token.')
    # Retain the original JSON API exemption; JSON requests require same-origin/CORS permission.
    origin = request.headers.get('Origin')
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme not in {'http', 'https'} or parsed.netloc.lower() != request.host.lower():
            abort(400, description='Cross-origin registration rejected.')
    data = _payload()
    if not isinstance(data, dict) or any(not isinstance(data.get(key, ''), str) for key in ('name', 'email', 'password')):
        return jsonify({'error': 'Invalid registration data.'}), 400
    errors, email = _validate_user(data)
    if len(data.get('name', '')) > 120 or len(email) > 255: errors.append('Name or email is too long.')
    limited = check_attempt('register', email)
    if limited is not None: return limited
    with get_session() as db:
        if db.scalar(select(User).where(func.lower(User.email) == email)): errors.append("Email is already registered.")
        if errors:
            if request.is_json: return jsonify({'errors': errors}), 400
            return render_template('register.html', registration_csrf=token, registration_values={'name': data.get('name',''), 'email': email}, registration_error=' '.join(errors)), 400
        user = User(name=data["name"].strip(), email=email, role="user"); user.set_password(data["password"])
        from super_admin.service import audit, snapshot
        try:
            db.add(user); db.flush()
            audit(db, user, 'auth.registration', user, after=snapshot(user), ip=request.remote_addr)
            db.commit()
        except IntegrityError:
            db.rollback()
            return jsonify({'errors': ['Email is already registered.']}), 400
        if not request.is_json: return redirect('/login?registered=1')
        return jsonify({"user": user.to_dict()}), 201


@bp.post("/logout")
def logout():
    session.clear(); return jsonify({"message": "Logged out."})


@bp.get("/me")
def me():
    user = current_user()
    if not user: return jsonify({"error": "Authentication required."}), 401
    return jsonify({"user": user.to_dict(), "csrf_token": session.get("csrf_token")})


def admin_required():
    user = current_user()
    if not user or user.role != "admin": return None
    return user


@bp.get("/users")
def users():
    if not admin_required(): return jsonify({"error": "Admin access required."}), 403
    with get_session() as db: return jsonify({"users": [u.to_dict() for u in db.scalars(select(User).where(User.deleted_at.is_(None)).order_by(User.name))]})


@bp.post("/users")
def create_user():
    if not admin_required(): return jsonify({"error": "Admin access required."}), 403
    data = _payload(); errors, email = _validate_user(data)
    if data.get("role") == "super_admin": return jsonify({"error": "Only Super Admin can create a Super Admin."}), 403
    with get_session() as db:
        if db.scalar(select(User).where(func.lower(User.email) == email)): errors.append("Email is already registered.")
        if errors: return jsonify({"errors": errors}), 400
        user = User(name=data["name"].strip(), email=email, role=data.get("role", "user") if data.get("role") in {"admin", "user"} else "user")
        user.set_password(data["password"]); db.add(user); db.commit(); return jsonify({"user": user.to_dict()}), 201


@bp.patch("/users/<int:user_id>")
def update_user(user_id):
    if not admin_required(): return jsonify({"error": "Admin access required."}), 403
    data = _payload()
    with get_session() as db:
        user = db.get(User, user_id)
        if not user or user.deleted_at: return jsonify({"error": "User not found."}), 404
        if user.role == "super_admin" or data.get("role") == "super_admin":
            return jsonify({"error": "Only Super Admin can change a Super Admin."}), 403
        if data.get("name"): user.name = data["name"].strip()
        if data.get("role") in {"admin", "user"}: user.role = data["role"]
        if data.get("password"):
            if len(data["password"]) < 8: return jsonify({"error": "Password must be at least 8 characters."}), 400
            user.set_password(data["password"])
        db.commit(); return jsonify({"user": user.to_dict()})


@bp.delete("/users/<int:user_id>")
def delete_user(user_id):
    admin = admin_required()
    if not admin: return jsonify({"error": "Admin access required."}), 403
    if user_id == admin.id: return jsonify({"error": "You cannot delete your own account."}), 400
    with get_session() as db:
        user = db.get(User, user_id)
        if not user or user.deleted_at: return jsonify({"error": "User not found."}), 404
        if user.role == "super_admin": return jsonify({"error": "Only Super Admin can change a Super Admin."}), 403
        from companies.models import Company
        if db.scalar(select(Company.id).where(Company.owner_user_id == user_id)):
            return jsonify({'error': 'A company owner cannot be hard-deleted. Use Super Admin soft delete.'}), 409
        from super_admin.service import detach_legacy_deleted_user
        detach_legacy_deleted_user(db, user_id)
        db.delete(user); db.commit(); return jsonify({"message": "User deleted."})
