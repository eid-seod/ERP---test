"""Step 3 acceptance tests: composed, bilingual company chart of accounts.

All fixtures use a temporary platform database and an external temporary
company-data root.  This module never imports or touches the production database.
"""

import secrets

import pytest
from sqlalchemy import select

import database
from companies.chart_config import (
    ACTIVITY_ACCOUNTS, BASE_ACCOUNTS, LEGAL_ACCOUNTS, ChartError,
    build_chart, chart_composition,
)
from companies.config import COMPANY_TYPES, LEGAL_FORMS
from companies.models import Company
from models.user import User

BASE_CODES = {row[0] for row in BASE_ACCOUNTS}


def _create_app(config):
    from app import create_app
    return create_app(config)


@pytest.fixture()
def company_app(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", secrets.token_urlsafe(18))
    return _create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "DATABASE_URL": "sqlite:///" + str(tmp_path / "platform.db"),
            "COMPANY_DATA_DIR": str(tmp_path / "company-data"),
        }
    )


def sign_in(app, identity):
    client = app.test_client()
    response = client.post("/login", json=identity)
    assert response.status_code == 200, response.get_data(as_text=True)
    return client, {"X-CSRF-Token": response.get_json()["csrf_token"]}


@pytest.fixture()
def owner(company_app):
    password = secrets.token_urlsafe(18)
    with database.get_session() as db:
        user = User(name="ChartOwner", email="chart-owner@fixture.invalid", role="user")
        user.set_password(password)
        db.add(user)
        db.commit()
        user_id = user.id
    return {"id": user_id, "email": "chart-owner@fixture.invalid", "password": password}


def create_company(client, headers, **changes):
    payload = {
        "name": "Chart Fixture",
        "company_type": "industrial",
        "legal_form": "sole_proprietorship",
        "base_currency": "EGP",
        "fiscal_year_start_month": 1,
    }
    payload.update(changes)
    response = client.post("/companies/new", json=payload, headers=headers)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()["company"]["id"]


def test_chart_is_composed_from_base_activity_and_legal_layers():
    for company_type in COMPANY_TYPES:
        for legal_form in LEGAL_FORMS:
            chart = build_chart(company_type, legal_form)
            codes = [row["code"] for row in chart]
            assert len(codes) == len(set(codes)), "no duplicate codes"
            composition = chart_composition(company_type, legal_form)
            # Base layer is identical for every company.
            assert set(composition["base"]) == BASE_CODES
            # Exactly one activity pack and one legal-form layer contribute.
            assert set(composition["activity"]) == {row[0] for row in ACTIVITY_ACCOUNTS[company_type]}
            assert set(composition["legal_form"]) == {row[0] for row in LEGAL_ACCOUNTS[legal_form]}
            # A composed chart is not a fixed count shared by all six combinations.
            assert len(chart) == len(BASE_ACCOUNTS) + len(ACTIVITY_ACCOUNTS[company_type]) + len(LEGAL_ACCOUNTS[legal_form])


def test_account_names_are_bilingual_with_arabic_primary():
    for row in build_chart("trading", "joint_stock"):
        assert row["name_ar"].strip() and row["name_en"].strip()
        # Arabic primary name actually contains Arabic letters.
        assert any("\u0600" <= char <= "\u06ff" for char in row["name_ar"])


def test_activity_pack_differs_between_company_types():
    industrial = set(chart_composition("industrial", "sole_proprietorship")["activity"])
    trading = set(chart_composition("trading", "sole_proprietorship")["activity"])
    contracting = set(chart_composition("contracting", "sole_proprietorship")["activity"])
    assert industrial != trading != contracting
    assert industrial != contracting


def test_legal_form_layer_differs_between_legal_forms():
    sole = set(chart_composition("trading", "sole_proprietorship")["legal_form"])
    joint = set(chart_composition("trading", "joint_stock")["legal_form"])
    assert sole != joint
    assert joint == {row[0] for row in LEGAL_ACCOUNTS["joint_stock"]}


def test_chart_rejects_unknown_type_or_legal_form():
    with pytest.raises(ChartError):
        build_chart("invalid", "sole_proprietorship")
    with pytest.raises(ChartError):
        build_chart("trading", "invalid")


def test_owner_reads_own_composed_chart_from_workspace(company_app, owner):
    client, headers = sign_in(company_app, owner)
    company_id = create_company(client, headers, company_type="trading", legal_form="joint_stock")
    response = client.get(f"/companies/{company_id}/chart-of-accounts")
    assert response.status_code == 200
    accounts = response.get_json()["accounts"]
    assert [row["code"] for row in accounts] == [row["code"] for row in build_chart("trading", "joint_stock")]
    assert all("name_ar" in row and "name_en" in row for row in accounts)
    page = client.get(f"/companies/{company_id}")
    assert page.status_code == 200 and 'dir="rtl"' in page.text
    assert "شجرة الحسابات" in page.text


def test_chart_reflects_created_company_type_and_legal_form(company_app, owner):
    client, headers = sign_in(company_app, owner)
    company_id = create_company(client, headers, company_type="contracting", legal_form="sole_proprietorship")
    accounts = client.get(f"/companies/{company_id}/chart-of-accounts").get_json()["accounts"]
    packs = {row["pack"] for row in accounts}
    assert packs == {"base", "activity", "legal_form"}
    assert {row["code"] for row in accounts if row["pack"] == "activity"} == {
        row[0] for row in ACTIVITY_ACCOUNTS["contracting"]
    }


def test_other_user_cannot_read_chart(company_app, owner):
    client, headers = sign_in(company_app, owner)
    company_id = create_company(client, headers)
    password = secrets.token_urlsafe(18)
    with database.get_session() as db:
        other = User(name="OtherOwner", email="other-owner@fixture.invalid", role="user")
        other.set_password(password)
        db.add(other)
        db.commit()
    other_client, _ = sign_in(company_app, {"email": "other-owner@fixture.invalid", "password": password})
    assert other_client.get(f"/companies/{company_id}/chart-of-accounts").status_code == 403


def test_chart_route_requires_authentication(company_app, owner):
    client, headers = sign_in(company_app, owner)
    company_id = create_company(client, headers)
    anonymous = company_app.test_client()
    response = anonymous.get(f"/companies/{company_id}/chart-of-accounts")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_super_admin_cannot_read_company_chart(company_app, owner):
    client, headers = sign_in(company_app, owner)
    company_id = create_company(client, headers)
    password = secrets.token_urlsafe(18)
    with database.get_session() as db:
        super_user = User(name="ChartSuper", email="chart-super@fixture.invalid", role="super_admin")
        super_user.set_password(password)
        db.add(super_user)
        db.commit()
    super_client = company_app.test_client()
    login = super_client.post("/super-admin/login", json={"email": "chart-super@fixture.invalid", "password": password})
    assert login.status_code == 200, login.get_data(as_text=True)
    assert super_client.get(f"/companies/{company_id}/chart-of-accounts").status_code == 403
