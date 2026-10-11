"""Step 3A tests: versioned JSON account packs, validator and composer.

Data + validator only; no database and no UI are exercised here.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = ROOT / "packs"
if str(PACKS_DIR) not in sys.path:
    sys.path.insert(0, str(PACKS_DIR))

import compose  # noqa: E402
import validate  # noqa: E402

from companies.chart_config import build_chart, chart_composition  # noqa: E402
from companies.config import COMPANY_TYPES, LEGAL_FORMS  # noqa: E402


def test_every_pack_file_exists_with_version_and_accounts():
    for name in validate.PACK_NAMES:
        document = json.loads((PACKS_DIR / name).read_text(encoding="utf-8"))
        assert document["version"] == "1.0.0"
        assert isinstance(document["accounts"], list) and document["accounts"]


def test_all_packs_validate_and_required_fields_present():
    result = validate.validate_packs()
    for name, pack in result["packs"].items():
        for code, account in pack["accounts"].items():
            for field in validate.REQUIRED_FIELDS:
                assert field in account, f"{name}:{code} missing {field}"


def test_codes_are_unique_within_pack_and_disjoint_across_co_occurring_packs():
    result = validate.validate_packs()
    # Two activity packs never co-occur, and two legal-form layers never co-occur,
    # so the base pack must be disjoint from each of them.
    base = set(result["packs"][validate.BASE_PACK]["accounts"])
    for activity_pack in validate.ACTIVITY_PACKS.values():
        assert not (base & set(result["packs"][activity_pack]["accounts"]))
    for legal_pack in validate.LEGAL_FORM_PACKS.values():
        assert not (base & set(result["packs"][legal_pack]["accounts"]))


def test_all_six_compositions_are_valid():
    result = validate.validate_packs()
    assert len(result["compositions"]) == len(COMPANY_TYPES) * len(LEGAL_FORMS) == 6
    for (activity, legal_form), merged in result["compositions"].items():
        codes = set(merged)
        children = {}
        for code, account in merged.items():
            if account["parent"] is not None:
                assert account["parent"] in codes
                assert merged[account["parent"]]["type"] == account["type"]
                children.setdefault(account["parent"], []).append(code)
        for code, account in merged.items():
            if code in children:
                assert not account["is_postable"], f"{code} postable but has children"


def test_six_compositions_are_distinct():
    charts = {
        (activity, legal_form): tuple(row["code"] for row in compose.compose_chart(activity, legal_form))
        for activity in compose.ACTIVITY_TYPES
        for legal_form in compose.LEGAL_FORMS
    }
    assert len(set(charts.values())) == 6


def test_equity_layer_differs_by_legal_form():
    sole = {row["code"] for row in compose.compose_chart("trading", "sole_proprietorship") if row["type"] == "equity"}
    joint = {row["code"] for row in compose.compose_chart("trading", "joint_stock") if row["type"] == "equity"}
    assert sole != joint
    # Both legal forms define the shared gravity of the equity group differently.
    assert "3100" in sole and "3200" in joint


def test_equity_group_codes_come_only_from_legal_form_layer():
    for activity in compose.ACTIVITY_TYPES:
        for legal_form in compose.LEGAL_FORMS:
            for row in compose.compose_chart(activity, legal_form):
                if row["type"] == "equity":
                    assert row["layer"] == compose.LAYER_LEGAL_FORM


def test_composition_is_deterministic():
    for activity in compose.ACTIVITY_TYPES:
        for legal_form in compose.LEGAL_FORMS:
            first = compose.compose_chart(activity, legal_form)
            second = compose.compose_chart(activity, legal_form)
            assert first == second
            codes = [row["code"] for row in first]
            assert codes == sorted(codes)


def test_postable_accounts_are_always_leaves():
    for activity in compose.ACTIVITY_TYPES:
        for legal_form in compose.LEGAL_FORMS:
            rows = compose.compose_chart(activity, legal_form)
            parents = {row["parent"] for row in rows if row["parent"]}
            for row in rows:
                if row["is_postable"]:
                    assert row["code"] not in parents


def test_expected_system_accounts_are_present():
    rows = compose.compose_chart("trading", "sole_proprietorship")
    system_names = {row["name_en"] for row in rows if row["is_system"]}
    for expected in (
        "Customers (control)", "Suppliers (control)", "VAT input (recoverable)",
        "VAT output (payable)", "VAT settlement", "Withholding tax receivable",
        "Withholding tax payable", "Retained earnings",
        "Foreign exchange gain - realized", "Foreign exchange loss - realized",
    ):
        assert expected in system_names


def test_chart_config_facade_matches_pack_composition():
    for activity in COMPANY_TYPES:
        for legal_form in LEGAL_FORMS:
            facade = build_chart(activity, legal_form)
            composed = compose.compose_chart(activity, legal_form)
            assert [row["code"] for row in facade] == [row["code"] for row in composed]
            assert {row["pack"] for row in facade} == {"base", "activity", "legal_form"}
            composition = chart_composition(activity, legal_form)
            assert set(composition["base"]).isdisjoint(composition["activity"])
            assert set(composition["base"]).isdisjoint(composition["legal_form"])


def test_validator_script_runs_and_reports_success():
    result = subprocess.run(
        [sys.executable, str(PACKS_DIR / "validate.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_pack_codes_follow_numbering_groups():
    result = validate.validate_packs()
    for name, pack in result["packs"].items():
        for code, account in pack["accounts"].items():
            allowed = validate.NUMBERING[code[0]]
            assert account["type"] in allowed, f"{name}:{code}"
