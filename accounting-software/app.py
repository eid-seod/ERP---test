import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select

from branding import PERSONAL_NAME, SOLUTION_NAME, SOLUTION_DESCRIPTION
from database import configure_database, get_session, init_db
from models.user import User
from routes.auth import bp as auth_bp
from routes.clients import bp as clients_bp
from routes.invoices import bp as invoices_bp
from super_admin import init_super_admin, require_existing_upgrade
from companies.integration import init_companies
from migrations.companies import require_existing_company_upgrade
from login_portals import bp as login_portals_bp, login_page as render_login_page


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE_URL=os.environ.get("DATABASE_URL", f"sqlite:///{Path(__file__).with_name('database.db')}"),
        TOKEN_FACTORY=secrets.token_urlsafe,
    )
    if test_config: app.config.update(test_config)
    engine = configure_database(app.config["DATABASE_URL"])
    require_existing_upgrade(engine)
    with engine.connect() as connection:
        existing_tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        fresh = not existing_tables
        if existing_tables and 'users' not in existing_tables:
            raise RuntimeError('Existing platform schema is incomplete. Refusing automatic initialization.')
    require_existing_company_upgrade(engine)
    if fresh:
        init_db()
    else:
        from companies.platform_guard import require_existing_business_schema
        require_existing_business_schema(engine)
    init_super_admin(app)
    init_companies(app, fresh=fresh)

    @app.context_processor
    def personal_brand():
        return {
            "personal_name": PERSONAL_NAME,
            "solution_name": SOLUTION_NAME,
            "solution_description": SOLUTION_DESCRIPTION,
        }

    @app.before_request
    def csrf_protection():
        if request.method in {"POST", "PATCH", "PUT", "DELETE"} and request.path not in {"/login", "/register"} and request.path != "/logout":
            if request.path.startswith(("/invoices", "/clients", "/users")) and request.headers.get("X-CSRF-Token") != session.get("csrf_token"):
                return jsonify({"error": "Invalid CSRF token."}), 400

    app.register_blueprint(auth_bp); app.register_blueprint(clients_bp); app.register_blueprint(invoices_bp)
    app.register_blueprint(login_portals_bp)

    @app.get("/")
    def index(): return redirect(url_for("dashboard")) if session.get("user_id") else redirect(url_for("login_page"))

    @app.get("/login")
    def login_page(): return render_login_page('user')

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"): return redirect(url_for("login_page"))
        return render_template("dashboard.html")

    @app.get("/invoice/new")
    @app.get("/invoice/<int:invoice_id>/edit")
    def invoice_form(invoice_id=None):
        if not session.get("user_id"): return redirect(url_for("login_page"))
        return render_template("invoice_form.html", invoice_id=invoice_id)

    with get_session() as db:
        if not db.scalar(select(User).where(User.email == "admin@example.com")):
            if not fresh:
                raise RuntimeError('Existing platform database lacks its original administrator. Refusing automatic seeding.')
            admin = User(name="System Admin", email="admin@example.com", role="admin"); admin.set_password(os.environ.get("ADMIN_PASSWORD", "Admin123!")); db.add(admin); db.commit()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
