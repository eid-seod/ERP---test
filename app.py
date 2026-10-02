import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select

from database import configure_database, get_session, init_db
from models.user import User
from routes.auth import bp as auth_bp
from routes.clients import bp as clients_bp
from routes.invoices import bp as invoices_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE_URL=os.environ.get("DATABASE_URL", f"sqlite:///{Path(__file__).with_name('database.db')}"),
        TOKEN_FACTORY=secrets.token_urlsafe,
    )
    if test_config: app.config.update(test_config)
    configure_database(app.config["DATABASE_URL"]); init_db()

    @app.before_request
    def csrf_protection():
        if request.method in {"POST", "PATCH", "PUT", "DELETE"} and request.path not in {"/login", "/register"} and request.path != "/logout":
            if request.path.startswith(("/invoices", "/clients", "/users")) and request.headers.get("X-CSRF-Token") != session.get("csrf_token"):
                return jsonify({"error": "Invalid CSRF token."}), 400

    app.register_blueprint(auth_bp); app.register_blueprint(clients_bp); app.register_blueprint(invoices_bp)

    @app.get("/")
    def index(): return redirect(url_for("dashboard")) if session.get("user_id") else redirect(url_for("login_page"))

    @app.get("/login")
    def login_page(): return render_template("login.html")

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"): return redirect(url_for("login_page"))
        return render_template("dashboard.html")

    @app.get("/invoice/new")
    def invoice_form():
        if not session.get("user_id"): return redirect(url_for("login_page"))
        return render_template("invoice_form.html")

    with get_session() as db:
        if not db.scalar(select(User).where(User.email == "admin@example.com")):
            admin = User(name="System Admin", email="admin@example.com", role="admin"); admin.set_password(os.environ.get("ADMIN_PASSWORD", "Admin123!")); db.add(admin); db.commit()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
