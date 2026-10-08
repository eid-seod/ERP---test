"""Step 2 acceptance tests: registration, isolated companies, and Super Admin visibility.

All fixtures use a temporary platform database and an external temporary company-data
root.  This module intentionally does not import or touch the production database.
"""

import hashlib
import json
import re
import secrets
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import event, func, select

import database
from companies.config import COMPANY_TYPES, CURRENCIES, DEFAULT_COMPANY_DATA_DIR, LEGAL_FORMS, SCHEMA_VERSION
from companies.models import Company, CompanyMembership
from companies.storage import health_check
from migrations.companies import migrate_file as migrate_companies_file
from migrations.super_admin import migrate_file as migrate_step1_file
from models.user import User
from super_admin.models import PlatformSetting, UserAuditEvent


VALID_COMPANY = {
    "name": "Alpha Fixture",
    "company_type": "industrial",
    "legal_form": "sole_proprietorship",
    "base_currency": "EGP",
    "fiscal_year_start_month": 1,
    "tax_id": "VAT-ALPHA",
}


def _create_app(config):
    """Import lazily so merely collecting tests never touches the default DB."""
    from app import create_app
    return create_app(config)


@pytest.fixture()
def company_app(tmp_path, monkeypatch):
    """A fresh app whose platform and company files are both outside the repo."""
    admin_password = secrets.token_urlsafe(18)
    monkeypatch.setenv("ADMIN_PASSWORD", admin_password)
    app = _create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "DATABASE_URL": "sqlite:///" + str(tmp_path / "platform.db"),
            "COMPANY_DATA_DIR": str(tmp_path / "company-data"),
            "AUTH_ATTEMPT_LIMITS": {
                "login": {"ip": 30, "email": 30, "window": 300},
                "register": {"ip": 100, "email": 100, "window": 3600},
            },
        }
    )
    fixture_passwords = {}
    with database.get_session() as db:
        for name, email, role in (
            ("SuperoneAdmin", "superone@fixture.invalid", "super_admin"),
            ("standardA", "standard-a@fixture.invalid", "user"),
            ("standardB", "standard-b@fixture.invalid", "user"),
        ):
            password = secrets.token_urlsafe(18)
            fixture_passwords[name] = password
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.add(user)
            db.flush()
        db.commit()
    app.config["_TEST_FIXTURE_PASSWORDS"] = fixture_passwords
    app.config["_TEST_ADMIN_PASSWORD"] = admin_password
    return app


@pytest.fixture()
def identities(company_app):
    with database.get_session() as db:
        return {
            user.name: {"id": user.id, "email": user.email, "password": company_app.config["_TEST_FIXTURE_PASSWORDS"][user.name]}
            for user in db.scalars(select(User).where(User.email.like("%@fixture.invalid")))
        } | {
            "admin": {"id": db.scalar(select(User.id).where(User.email == "admin@example.com")), "email": "admin@example.com", "password": company_app.config["_TEST_ADMIN_PASSWORD"]}
        }


def sign_in(app, identity):
    client = app.test_client()
    response = client.post("/login", json={"email": identity["email"], "password": identity["password"]})
    assert response.status_code == 200, response.get_data(as_text=True)
    return client, {"X-CSRF-Token": response.get_json()["csrf_token"]}


def registration_enabled():
    with database.get_session() as db:
        row = db.get(PlatformSetting, "public_registration_enabled")
        if row is None:
            row = PlatformSetting(key="public_registration_enabled", value=True)
            db.add(row)
        else:
            row.value = True
        db.commit()


def platform_company(name):
    with database.get_session() as db:
        return db.scalar(select(Company).where(Company.name == name))


def company_id(name):
    company = platform_company(name)
    assert company is not None
    return company.id


def csrf_from_session(client):
    with client.session_transaction() as state:
        return state.get("csrf_token")


def create_company(client, headers, **changes):
    payload = dict(VALID_COMPANY)
    payload.update(changes)
    response = client.post("/companies/new", json=payload, headers=headers)
    return response, payload


def company_from_response(response):
    body = response.get_json(silent=True) or {}
    if "company" in body:
        return body["company"]
    match = re.search(r"/companies/(\d+)", response.headers.get("Location", ""))
    if match:
        return {"id": int(match.group(1))}
    return {}


def test_registration_is_off_by_default_and_on_has_native_arabic_page(company_app):
    public = company_app.test_client()
    assert public.get("/register").status_code == 404
    assert public.post("/register", json={"name": "Off", "email": "off@fixture.invalid", "password": secrets.token_urlsafe(18)}).status_code == 404
    registration_enabled()
    page = public.get("/register")
    assert page.status_code == 200
    assert 'dir="rtl"' in page.text
    assert any(word in page.text for word in ("التسجيل", "إنشاء", "حساب"))


def test_registration_json_is_standard_only_and_audited(company_app):
    registration_enabled()
    public = company_app.test_client()
    secret = secrets.token_urlsafe(18)
    response = public.post(
        "/register",
        json={"name": "Registered", "email": "REGISTERED@fixture.invalid", "password": secret, "role": "super_admin"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "registered@fixture.invalid"
    assert body["user"]["role"] == "user"
    assert "password_hash" not in json.dumps(body)
    with database.get_session() as db:
        user = db.scalar(select(User).where(User.email == "registered@fixture.invalid"))
        assert user.role == "user" and user.check_password(secret)
        event_row = db.scalar(select(UserAuditEvent).where(UserAuditEvent.action == "auth.registration").order_by(UserAuditEvent.id.desc()))
        assert event_row is not None
        assert secret not in (event_row.before_data + event_row.after_data)
        assert "password_hash" not in (event_row.before_data + event_row.after_data)


def test_registration_form_requires_csrf_and_accepts_valid_form(company_app):
    registration_enabled()
    public = company_app.test_client()
    assert public.post("/register", data={"name": "No CSRF", "email": "nocsrf@fixture.invalid", "password": secrets.token_urlsafe(18)}).status_code == 400
    secret = secrets.token_urlsafe(18)
    assert public.post(
        "/register", data={"name": "Form User", "email": "form@fixture.invalid", "password": secret, "csrf_token": csrf_from_session(public)},
    ).status_code == 302
    assert public.get("/login?registered=1").status_code == 200


@pytest.mark.parametrize("payload", [
    {"name": "", "email": "valid@fixture.invalid", "password": "x"},
    {"name": "Valid", "email": "not-an-email", "password": "x"},
    {"name": "Valid", "email": "short@fixture.invalid", "password": "x"},
])
def test_registration_validation(company_app, payload):
    registration_enabled()
    assert company_app.test_client().post("/register", json=payload).status_code == 400


def test_registration_duplicate_email_is_case_insensitive(company_app):
    registration_enabled()
    public = company_app.test_client()
    first = {"name": "First", "email": "Case@fixture.invalid", "password": secrets.token_urlsafe(18)}
    assert public.post("/register", json=first).status_code == 201
    assert public.post("/register", json={**first, "name": "Second", "email": "case@fixture.invalid"}).status_code == 400


def test_registration_and_login_throttles_are_configurable(company_app):
    registration_enabled()
    company_app.config["AUTH_ATTEMPT_LIMITS"] = {
        "login": {"ip": 2, "email": 2, "window": 3600},
        "register": {"ip": 2, "email": 1, "window": 3600},
    }
    public = company_app.test_client()
    body = {"name": "Throttle", "email": "throttle@fixture.invalid", "password": secrets.token_urlsafe(18)}
    assert public.post("/register", json=body).status_code == 201
    assert public.post("/register", json={**body, "email": "throttle2@fixture.invalid"}).status_code == 201
    limited = public.post("/register", json={**body, "email": "throttle3@fixture.invalid"})
    assert limited.status_code == 429 and limited.headers.get("Retry-After")
    for _ in range(2):
        assert public.post("/login", json={"email": "missing@fixture.invalid", "password": "wrong"}).status_code == 401
    assert public.post("/login", json={"email": "missing@fixture.invalid", "password": "wrong"}).status_code == 429


def test_throttle_counts_email_across_ips_and_ip_across_emails(company_app):
    registration_enabled()
    company_app.config["AUTH_ATTEMPT_LIMITS"] = {
        "login": {"ip": 2, "email": 1, "window": 3600},
        "register": {"ip": 2, "email": 1, "window": 3600},
    }
    public = company_app.test_client()
    same_email = {"email": "dimension-email@fixture.invalid", "password": "wrong"}
    assert public.post("/login", json=same_email, environ_base={"REMOTE_ADDR": "192.0.2.1"}).status_code == 401
    assert public.post("/login", json=same_email, environ_base={"REMOTE_ADDR": "192.0.2.2"}).status_code == 429
    for email in ("dimension-ip-a@fixture.invalid", "dimension-ip-b@fixture.invalid"):
        assert public.post("/login", json={"email": email, "password": "wrong"}, environ_base={"REMOTE_ADDR": "192.0.2.10"}).status_code == 401
    assert public.post("/login", json={"email": "dimension-ip-c@fixture.invalid", "password": "wrong"}, environ_base={"REMOTE_ADDR": "192.0.2.10"}).status_code == 429


@pytest.mark.parametrize("method,path", [
    ("get", "/companies"), ("get", "/companies/new"),
    ("get", "/super-admin/companies"), ("post", "/super-admin/company-limit"),
])
def test_anonymous_company_routes_redirect_to_login(company_app, method, path):
    response = getattr(company_app.test_client(), method)(path, json={}) if method == "post" else getattr(company_app.test_client(), method)(path)
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


@pytest.mark.parametrize("role_key", ["admin", "SuperoneAdmin"])
def test_only_standard_users_can_use_company_routes(company_app, identities, role_key):
    client, headers = sign_in(company_app, identities[role_key])
    for path in ("/companies", "/companies/new"):
        assert client.get(path).status_code == 403
    assert client.post("/companies/new", json=VALID_COMPANY, headers=headers).status_code == 403
    assert client.get("/super-admin/companies").status_code == (200 if role_key == "SuperoneAdmin" else 403)
    assert client.post("/super-admin/company-limit", json={"maximum": 2}, headers=headers).status_code == (200 if role_key == "SuperoneAdmin" else 403)


def test_standard_user_can_list_and_open_only_own_company(company_app, identities):
    client_a, headers_a = sign_in(company_app, identities["standardA"])
    response, _ = create_company(client_a, headers_a)
    assert response.status_code in (201, 302)
    alpha = company_from_response(response)
    if "id" not in alpha:
        alpha["id"] = company_id("Alpha Fixture")
    listing = client_a.get("/companies", headers={"Accept": "application/json"})
    assert listing.status_code == 200
    assert alpha["id"] in {row["id"] for row in listing.get_json()["companies"]}
    workspace = client_a.get(f"/companies/{alpha['id']}", headers={"Accept": "application/json"})
    assert workspace.status_code == 200
    body = workspace.get_json()
    assert body.get("status", "active") == "active"
    safe = body.get("company", body)
    assert safe["name"] == "Alpha Fixture"
    assert "db_filename" not in json.dumps(body)
    assert "password_hash" not in json.dumps(body)


def test_company_creation_json_and_form_csrf_redirect(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    response, _ = create_company(client, headers)
    assert response.status_code == 201
    assert response.get_json()["company"]["status"] == "active"
    second, _ = create_company(client, headers, name="Second blocked")
    assert second.status_code == 409
    client_b, headers_b = sign_in(company_app, identities["standardB"])
    page = client_b.get("/companies/new")
    assert page.status_code == 200 and 'dir="rtl"' in page.text
    assert client_b.post("/companies/new", data=VALID_COMPANY).status_code == 400
    form_data = {**VALID_COMPANY, "name": "Bravo Form", "csrf_token": headers_b["X-CSRF-Token"]}
    form = client_b.post("/companies/new", data=form_data)
    assert form.status_code == 302
    assert "/companies/" in form.headers["Location"]


def test_every_company_mutation_requires_csrf(company_app, identities):
    standard, standard_headers = sign_in(company_app, identities["standardA"])
    assert standard.post("/companies/new", json=VALID_COMPANY).status_code == 400
    assert standard.post("/companies/new", json=VALID_COMPANY, headers={"X-CSRF-Token": "invalid"}).status_code == 400
    created, _ = create_company(standard, standard_headers, name="CSRF Fixture")
    cid = created.get_json()["company"]["id"]
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    for path, payload in (
        ("/super-admin/company-limit", {"maximum": 2}),
        (f"/super-admin/companies/{cid}/status", {"action": "suspend"}),
    ):
        assert super_client.post(path, json=payload).status_code == 400
        assert super_client.post(path, json=payload, headers={"X-CSRF-Token": "invalid"}).status_code == 400
        assert super_client.post(path, json=payload, headers=super_headers).status_code == 200


def test_default_company_data_root_is_outside_the_tracked_application(company_app):
    repo_root = Path(__file__).resolve().parents[1]
    assert not Path(DEFAULT_COMPANY_DATA_DIR).resolve().is_relative_to(repo_root)


@pytest.mark.parametrize("field,value", [
    ("company_type", "invalid"),
    ("legal_form", "invalid"),
    ("base_currency", "JPY"),
    ("fiscal_year_start_month", 0),
    ("fiscal_year_start_month", 13),
    ("fiscal_year_start_month", "1"),
])
def test_company_wizard_accepts_only_allowed_fields(company_app, identities, field, value):
    client, headers = sign_in(company_app, identities["standardA"])
    response, _ = create_company(client, headers, **{field: value})
    assert response.status_code == 400


def test_every_allowed_company_type_form_and_currency_is_accepted(company_app, identities):
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    assert super_client.post("/super-admin/company-limit", json={"maximum": len(COMPANY_TYPES) * len(LEGAL_FORMS) * len(CURRENCIES)}, headers=super_headers).status_code == 200
    client, headers = sign_in(company_app, identities["standardA"])
    index = 0
    for company_type in COMPANY_TYPES:
        for legal_form in LEGAL_FORMS:
            for currency in CURRENCIES:
                response, _ = create_company(client, headers, name=f"Allowed {index}", company_type=company_type, legal_form=legal_form, base_currency=currency)
                assert response.status_code == 201, response.get_data(as_text=True)
                index += 1


def test_company_wizard_rejects_invalid_name_and_tax_id(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    assert create_company(client, headers, name=" ")[0].status_code == 400
    assert create_company(client, headers, tax_id=[])[0].status_code == 400
    assert create_company(client, headers, tax_id="x" * 81)[0].status_code == 400


def test_unknown_fields_cannot_grant_permissions_or_control_filename(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    payload = dict(VALID_COMPANY, name="Unknown Field Fixture", role="super_admin", owner_user_id=identities["SuperoneAdmin"]["id"], status="active", db_filename="../../outside.db")
    response = client.post("/companies/new", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.get_json()["company"]
    assert body["owner_user_id"] == identities["standardA"]["id"]
    assert body["status"] == "active"
    assert "db_filename" not in body
    with database.get_session() as db:
        assert db.get(User, identities["standardA"]["id"]).role == "user"
        row = db.get(Company, body["id"])
        assert Path(row.db_filename).name == row.db_filename and ".." not in row.db_filename


def test_provisioning_creates_generated_file_safe_schema_and_no_sensitive_filenames(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    response, _ = create_company(client, headers, name="Schema Fixture")
    assert response.status_code == 201
    with database.get_session() as db:
        row = db.get(Company, response.get_json()["company"]["id"])
        filename = row.db_filename
    root = Path(company_app.config["COMPANY_DATA_DIR"]).resolve()
    path = (root / filename).resolve()
    assert path.parent == root and path.is_file() and not path.is_symlink()
    assert path.name != "Schema Fixture.db" and "Schema Fixture" not in path.name
    with sqlite3.connect(path) as connection:
        tables = {name for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert tables == {"schema_meta", "company_settings"}
        assert connection.execute("SELECT version FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
        settings = connection.execute("SELECT name,type,legal_form,base_currency,country,currency_locked FROM company_settings").fetchone()
        assert settings == ("Schema Fixture", "industrial", "sole_proprietorship", "EGP", "Egypt", 0)


def test_two_companies_are_isolated_and_guessing_other_id_is_denied(company_app, identities):
    client_a, headers_a = sign_in(company_app, identities["standardA"])
    a, _ = create_company(client_a, headers_a, name="Isolation A", tax_id="A-TAX")
    assert a.status_code == 201
    client_b, headers_b = sign_in(company_app, identities["standardB"])
    b, _ = create_company(client_b, headers_b, name="Isolation B", tax_id="B-TAX", base_currency="USD")
    assert b.status_code == 201
    aid, bid = a.get_json()["company"]["id"], b.get_json()["company"]["id"]
    assert client_a.get(f"/companies/{bid}").status_code == 403
    assert client_b.get(f"/companies/{aid}").status_code == 403
    with database.get_session() as db:
        denied = db.scalar(select(UserAuditEvent).where(UserAuditEvent.action == "workspace.denied").order_by(UserAuditEvent.id.desc()))
        assert denied.actor_id == identities["standardB"]["id"]
        assert denied.target_id == identities["standardB"]["id"]
        assert identities["standardA"]["id"] not in json.loads(denied.after_data).values()
    root = Path(company_app.config["COMPANY_DATA_DIR"])
    for name, own, foreign in (("Isolation A", "A-TAX", "B-TAX"), ("Isolation B", "B-TAX", "A-TAX")):
        row = platform_company(name)
        with sqlite3.connect(root / row.db_filename) as connection:
            values = connection.execute("SELECT name,tax_id FROM company_settings").fetchone()
            assert values == (name, own)
            assert foreign not in json.dumps(values)


def test_admin_and_super_admin_cannot_open_workspace_even_with_membership(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(client, headers, name="No Admin Workspace")
    cid = created.get_json()["company"]["id"]
    with database.get_session() as db:
        db.add(CompanyMembership(user_id=identities["SuperoneAdmin"]["id"], company_id=cid, role="owner", status="active"))
        db.add(CompanyMembership(user_id=identities["admin"]["id"], company_id=cid, role="owner", status="active"))
        db.commit()
    for key in ("admin", "SuperoneAdmin"):
        other, _ = sign_in(company_app, identities[key])
        assert other.get(f"/companies/{cid}").status_code == 403


def test_company_limit_setting_is_integer_and_audited(company_app, identities):
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    assert super_client.post("/super-admin/company-limit", json={"maximum": 2}, headers=super_headers).status_code == 200
    with database.get_session() as db:
        setting = db.get(PlatformSetting, "max_companies_per_user")
        assert setting.integer_value == 2
    standard, standard_headers = sign_in(company_app, identities["standardA"])
    assert create_company(standard, standard_headers, name="Limit One")[0].status_code == 201
    assert create_company(standard, standard_headers, name="Limit Two")[0].status_code == 201
    assert create_company(standard, standard_headers, name="Limit Three")[0].status_code == 409
    events = super_client.get("/super-admin/audit?action=companies.limit_changed", headers={"Accept": "application/json"}).get_json()["events"]
    assert events and events[0]["after"]["maximum"] == 2


def test_company_limit_race_never_creates_two_when_limit_is_one(company_app, identities):
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    assert super_client.post("/super-admin/company-limit", json={"maximum": 1}, headers=super_headers).status_code == 200

    def attempt(index):
        client, headers = sign_in(company_app, identities["standardA"])
        return client.post("/companies/new", json={**VALID_COMPANY, "name": f"Race {index}"}, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(attempt, range(2)))
    assert statuses.count(201) == 1
    assert all(status in {201, 409, 503} for status in statuses)
    with database.get_session() as db:
        assert db.scalar(select(func.count(Company.id)).where(Company.owner_user_id == identities["standardA"]["id"], Company.status == "active")) == 1
    files = list(Path(company_app.config["COMPANY_DATA_DIR"]).glob("*.db"))
    assert len(files) == 1


@pytest.mark.parametrize("stage", ["temp_created", "schema_applied", "settings_written", "file_moved", "before_commit"])
def test_each_provisioning_stage_failure_cleans_files_registry_and_audits(company_app, identities, stage):
    def fail(current_stage):
        if current_stage == stage:
            raise RuntimeError("forced failure at " + stage)

    company_app.config["COMPANY_PROVISION_HOOK"] = fail
    client, headers = sign_in(company_app, identities["standardA"])
    response, _ = create_company(client, headers, name="Failure " + stage)
    assert response.status_code in {400, 409, 500, 503}
    body = response.get_json(silent=True) or {}
    assert "traceback" not in json.dumps(body).lower()
    assert str(company_app.config["COMPANY_DATA_DIR"]) not in json.dumps(body)
    with database.get_session() as db:
        assert db.scalar(select(func.count(Company.id)).where(Company.name == "Failure " + stage, Company.status == "active")) == 0
        audit_row = db.scalar(select(UserAuditEvent).where(UserAuditEvent.action == "company.create_failed").order_by(UserAuditEvent.id.desc()))
        assert audit_row is not None
        assert "forced failure" not in audit_row.after_data
    root = Path(company_app.config["COMPANY_DATA_DIR"])
    assert not list(root.glob("*.db"))
    assert not list(root.glob("*.db.tmp"))


def test_path_traversal_and_symlink_targets_are_rejected(company_app, identities, monkeypatch):
    client, headers = sign_in(company_app, identities["standardA"])
    # User-supplied names must never become paths; an injected generated path is rejected too.
    response, _ = create_company(client, headers, name="../../traversal")
    assert response.status_code == 201
    row = platform_company("../../traversal")
    assert row is not None and Path(row.db_filename).name == row.db_filename
    root = Path(company_app.config["COMPANY_DATA_DIR"])
    outside = company_app.config["COMPANY_DATA_DIR"] + "-outside"
    Path(outside).mkdir()
    generated_name = "company-" + str(uuid.uuid4()) + ".db"
    link = root / generated_name
    link.symlink_to(Path(outside))
    from companies import storage
    monkeypatch.setattr(storage, "_generated_filename", lambda: generated_name)
    client_b, headers_b = sign_in(company_app, identities["standardB"])
    bad = client_b.post("/companies/new", json={**VALID_COMPANY, "name": "Symlink attempt"}, headers=headers_b)
    assert bad.status_code in {400, 409, 500, 503}
    assert not (Path(outside) / generated_name).exists()


def test_workspace_is_blocked_when_user_deactivated_or_company_suspended(company_app, identities):
    standard, standard_headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(standard, standard_headers, name="Lifecycle Fixture")
    cid = created.get_json()["company"]["id"]
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    assert super_client.post(f"/super-admin/companies/{cid}/status", json={"action": "suspend"}, headers=super_headers).status_code == 200
    assert standard.get(f"/companies/{cid}").status_code == 403
    assert super_client.post(f"/super-admin/companies/{cid}/status", json={"action": "reactivate"}, headers=super_headers).status_code == 200
    assert super_client.post(f"/super-admin/users/{identities['standardA']['id']}/status", json={"action": "deactivate"}, headers=super_headers).status_code == 200
    assert standard.get(f"/companies/{cid}").status_code in {302, 401, 403}
    actions = super_client.get("/super-admin/audit", headers={"Accept": "application/json"}).get_json()["events"]
    assert {event["action"] for event in actions} >= {"company.suspended", "company.reactivated"}


def test_super_admin_company_list_detail_filters_pagination_and_metadata_only(company_app, identities):
    standard, standard_headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(standard, standard_headers, name="Search Industrial", company_type="industrial")
    cid = created.get_json()["company"]["id"]
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(database._engine, "before_cursor_execute", capture)
    try:
        response = super_client.get("/super-admin/companies?q=Search&type=industrial&status=active&page=1&per_page=10", headers={"Accept": "application/json"})
        assert response.status_code == 200
        assert response.get_json()["companies"][0]["id"] == cid
        detail = super_client.get(f"/super-admin/companies/{cid}", headers={"Accept": "application/json"})
        assert detail.status_code == 200
        assert "company_settings" not in json.dumps(detail.get_json())
        assert "db_filename" not in json.dumps(detail.get_json())
    finally:
        event.remove(database._engine, "before_cursor_execute", capture)
    # Registry pages may check health, but must not query company settings or financial tables.
    assert not any(re.search(r"\b(company_settings|invoices|clients|invoice_items)\b", statement) for statement in statements)


def test_health_check_reads_only_schema_meta_via_read_only_connection(company_app, identities, monkeypatch):
    client, headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(client, headers, name="Health Fixture")
    row = platform_company("Health Fixture")
    calls = []
    from companies import storage
    original_connect = storage.sqlite3.connect

    class TrackingConnection:
        def __init__(self, connection):
            self._connection = connection

        def execute(self, sql, *args, **kwargs):
            calls.append(str(sql).lower())
            return self._connection.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._connection, name)

    def tracking_connect(*args, **kwargs):
        return TrackingConnection(original_connect(*args, **kwargs))

    monkeypatch.setattr(storage.sqlite3, "connect", tracking_connect)
    with company_app.app_context():
        result = health_check(row.id)
    assert result["healthy"] is True
    assert any("schema_meta" in query for query in calls)
    assert not any("company_settings" in query or "invoices" in query or "clients" in query for query in calls)


def test_health_check_reports_missing_file_and_schema_version_mismatch(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(client, headers, name="Health Failure Fixture")
    row = platform_company("Health Failure Fixture")
    path = Path(company_app.config["COMPANY_DATA_DIR"]) / row.db_filename
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE schema_meta SET version = 999")
    with company_app.app_context():
        mismatch = health_check(row)
    assert mismatch["file_exists"] and not mismatch["schema_version_matches"] and not mismatch["healthy"]
    path.unlink()
    with company_app.app_context():
        missing = health_check(row)
    assert missing == {"file_exists": False, "readable": False, "schema_version_matches": False, "healthy": False}


def test_audit_events_never_contain_passwords_or_hashes(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    secret = "Never-Log-This-Company-Secret!"
    response = client.post("/companies/new", json={**VALID_COMPANY, "name": "Audit Secret", "tax_id": secret}, headers=headers)
    assert response.status_code == 201
    with database.get_session() as db:
        events = list(db.scalars(select(UserAuditEvent).where(UserAuditEvent.action.like("company.%"))))
    dump = json.dumps([{"before": event.before_data, "after": event.after_data} for event in events])
    assert "password" not in dump.lower()
    assert "password_hash" not in dump.lower()
    assert secret in dump  # tax metadata is allowed; credentials are not


def test_owner_hard_delete_is_blocked_but_nonowner_normal_user_deletes(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(client, headers, name="Delete Fixture")
    cid = created.get_json()["company"]["id"]
    admin_client, admin_headers = sign_in(company_app, identities["admin"])
    owner_delete = admin_client.delete(f"/users/{identities['standardA']['id']}", json={}, headers=admin_headers)
    assert owner_delete.status_code == 409
    normal_delete = admin_client.delete(f"/users/{identities['standardB']['id']}", json={}, headers=admin_headers)
    assert normal_delete.status_code == 200
    super_client, super_headers = sign_in(company_app, identities["SuperoneAdmin"])
    assert super_client.post(f"/super-admin/users/{identities['standardA']['id']}/delete", json={}, headers=super_headers).status_code == 200
    assert client.get(f"/companies/{cid}").status_code == 302
    with database.get_session() as db:
        company = db.get(Company, cid)
        assert company is not None


def test_companies_migration_is_standalone_idempotent_and_preserves_step1_data(tmp_path):
    historical = tmp_path / "historical.db"
    password_hash = "werkzeug-preserved-hash"
    with sqlite3.connect(historical) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)")
        connection.execute("INSERT INTO users VALUES (1,'Historical','historical@fixture.invalid',?,'user',1,'2025-01-01')", (password_hash,))
        connection.execute("CREATE TABLE invoices(id INTEGER PRIMARY KEY, marker TEXT)")
        connection.execute("INSERT INTO invoices VALUES (1,'financial-row-preserved')")
    migrate_step1_file(historical)
    with sqlite3.connect(historical) as connection:
        connection.execute("INSERT OR REPLACE INTO platform_settings(key,value,updated_at) VALUES ('public_registration_enabled',0,CURRENT_TIMESTAMP)")
        before = connection.execute("SELECT id,name,email,password_hash,role,is_active FROM users").fetchone()
        invoice_before = connection.execute("SELECT marker FROM invoices").fetchone()
    copy = tmp_path / "received-copy.db"
    copy.write_bytes(historical.read_bytes())
    migrate_companies_file(copy)
    first_digest = hashlib.sha256(copy.read_bytes()).hexdigest()
    migrate_companies_file(copy)
    assert copy.exists()
    with sqlite3.connect(copy) as connection:
        assert connection.execute("SELECT id,name,email,password_hash,role,is_active FROM users").fetchone() == before
        assert connection.execute("SELECT marker FROM invoices").fetchone() == invoice_before
        assert connection.execute("SELECT value FROM platform_settings WHERE key='public_registration_enabled'").fetchone()[0] == 0
        assert connection.execute("SELECT integer_value FROM platform_settings WHERE key='max_companies_per_user'").fetchone()[0] == 1
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} >= {"companies", "company_memberships"}
    assert hashlib.sha256(copy.read_bytes()).hexdigest() == first_digest
    missing = tmp_path / "does-not-exist.db"
    with pytest.raises(RuntimeError):
        migrate_companies_file(missing)
    assert not missing.exists()


def test_existing_step1_database_requires_explicit_step2_migration_without_writes(tmp_path):
    path = tmp_path / "step1-only.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)")
        connection.execute("INSERT INTO users VALUES (1,'Historical','old@fixture.invalid','hash','user',1,'2025-01-01')")
    migrate_step1_file(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match="explicit Step 2 migration"):
        _create_app({"TESTING": True, "SECRET_KEY": "migration", "DATABASE_URL": "sqlite:///" + str(path), "COMPANY_DATA_DIR": str(tmp_path / "companies")})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "companies" not in tables and "company_memberships" not in tables


def test_existing_malformed_step2_registry_is_rejected_without_bytes_changes(tmp_path):
    path = tmp_path / "malformed-step2.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)")
        connection.execute("INSERT INTO users VALUES (1,'Historical','malformed@fixture.invalid','hash','user',1,'2025-01-01')")
    migrate_step1_file(path)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE companies(id INTEGER PRIMARY KEY, name TEXT)")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError):
        _create_app({"TESTING": True, "SECRET_KEY": "malformed", "DATABASE_URL": "sqlite:///" + str(path), "COMPANY_DATA_DIR": str(tmp_path / "companies")})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("bad_maximum", [0, None, "invalid", 101])
def test_existing_invalid_company_limit_is_rejected_without_writes(tmp_path, bad_maximum):
    path = tmp_path / "invalid-limit.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)")
        connection.execute("INSERT INTO users VALUES (1,'Historical','limit@fixture.invalid','hash','user',1,'2025-01-01')")
    migrate_step1_file(path)
    migrate_companies_file(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE platform_settings SET integer_value=? WHERE key='max_companies_per_user'", (bad_maximum,))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError):
        _create_app({"TESTING": True, "SECRET_KEY": "invalid-limit", "DATABASE_URL": "sqlite:///" + str(path), "COMPANY_DATA_DIR": str(tmp_path / "companies")})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_explicit_company_migration_refuses_malformed_existing_table_without_writes(tmp_path):
    path = tmp_path / "malformed-migration.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)")
        connection.execute("INSERT INTO users VALUES (1,'Historical','migration@fixture.invalid','hash','user',1,'2025-01-01')")
    migrate_step1_file(path)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE companies(id INTEGER PRIMARY KEY, name TEXT)")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError):
        migrate_companies_file(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_nonnumeric_company_schema_version_is_a_safe_unavailable_response(company_app, identities):
    client, headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(client, headers, name="Malformed Version")
    row = platform_company("Malformed Version")
    path = Path(company_app.config["COMPANY_DATA_DIR"]) / row.db_filename
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE schema_meta")
        connection.execute("CREATE TABLE schema_meta(version TEXT, applied_at TEXT)")
        connection.execute("INSERT INTO schema_meta VALUES ('not-a-version',CURRENT_TIMESTAMP)")
    response = client.get(f"/companies/{created.get_json()['company']['id']}", headers={"Accept": "application/json"})
    assert response.status_code == 503
    assert str(company_app.config["COMPANY_DATA_DIR"]) not in response.get_data(as_text=True)
    assert "traceback" not in response.get_data(as_text=True).lower()


def test_filename_collision_does_not_delete_preexisting_company_file(company_app, identities, monkeypatch):
    owner, owner_headers = sign_in(company_app, identities["standardA"])
    created, _ = create_company(owner, owner_headers, name="Collision Original")
    original = platform_company("Collision Original")
    path = Path(company_app.config["COMPANY_DATA_DIR"]) / original.db_filename
    original_bytes = path.read_bytes()
    from companies import storage
    monkeypatch.setattr(storage, "_generated_filename", lambda: original.db_filename)
    other, other_headers = sign_in(company_app, identities["standardB"])
    failed = other.post("/companies/new", json={**VALID_COMPANY, "name": "Collision Attempt"}, headers=other_headers)
    assert failed.status_code in {400, 409, 500, 503}
    assert path.is_file() and path.read_bytes() == original_bytes
    with database.get_session() as db:
        assert db.scalar(select(func.count(Company.id)).where(Company.name == "Collision Attempt", Company.status == "active")) == 0
