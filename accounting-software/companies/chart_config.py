"""Bilingual chart-of-accounts catalog, now backed by versioned JSON packs.

One company chart is *composed*, never authored as a separate per-company chart:

* a **base pack** shared by every company,
* exactly one **activity pack** chosen from the company type, and
* exactly one **legal-form layer** chosen from the legal form.

The catalog lives in ``accounting-software/packs/*.json`` (data) with the
validator/composer in ``packs/validate.py`` and ``packs/compose.py``.  This
module is a thin, back-compatible facade so existing routes/tests keep working:
it exposes the same public functions as before (``build_chart``,
``build_chart_rows``, ``chart_composition``, ``build_chart_rows``).

Account names are bilingual: Arabic is the primary (displayed) name and English
is the secondary name.
"""
import sys
from pathlib import Path

from .config import COMPANY_TYPES, LEGAL_FORMS

# Make the repository-root ``packs`` package importable as ``validate``/``compose``.
_PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"
if str(_PACKS_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKS_DIR))

import compose as _compose  # noqa: E402  (packs/compose.py)
import validate as _validate  # noqa: E402  (packs/validate.py)

# Account kinds.  Codes are grouped by kind so a composed chart stays readable.
ACCOUNT_KINDS = ("asset", "liability", "equity", "revenue", "expense")

PACK_BASE = _compose.LAYER_BASE
PACK_ACTIVITY = _compose.LAYER_ACTIVITY
PACK_LEGAL_FORM = _compose.LAYER_LEGAL_FORM
PACKS = (PACK_BASE, PACK_ACTIVITY, PACK_LEGAL_FORM)

PACK_LABELS = {
    PACK_BASE: "الحزمة الأساسية",
    PACK_ACTIVITY: "حزمة النشاط",
    PACK_LEGAL_FORM: "طبقة الشكل القانوني",
}

KIND_LABELS = {
    "asset": "أصول",
    "liability": "التزامات",
    "equity": "حقوق ملكية",
    "revenue": "إيرادات",
    "expense": "مصروفات",
}


class ChartError(Exception):
    """A chart could not be composed from the supplied type/legal form."""


def _catalog():
    """Load and validate the whole pack catalog (raises ChartError on problems)."""
    try:
        _validate.validate_packs()
    except _validate.PackError as exc:
        raise ChartError(str(exc)) from exc


def build_chart(company_type, legal_form):
    """Compose the three-layer chart for one company.

    Returns a list of dicts sorted by ``(code, layer)``.  ``pack`` records which
    layer contributed each account so the composition is explicit, and each row
    exposes the pack account fields used by the export/review tooling.
    """
    if company_type not in COMPANY_TYPES:
        raise ChartError("A valid company type is required to build the chart.")
    if legal_form not in LEGAL_FORMS:
        raise ChartError("A valid legal form is required to build the chart.")
    _catalog()
    try:
        composed = _compose.compose_chart(company_type, legal_form)
    except _compose.PackError as exc:
        raise ChartError(str(exc)) from exc
    rows = []
    for row in composed:
        rows.append(
            {
                "code": row["code"],
                "parent_code": row["parent"],
                "name_ar": row["name_ar"],
                "name_en": row["name_en"],
                "kind": row["type"],
                "pack": row["layer"],
                "sort_order": 0,
                "is_postable": row["is_postable"],
                "is_system": row["is_system"],
                "normal_balance": row["normal_balance"],
                "description": row["description"],
                "pack_version": row["pack_version"],
            }
        )
    return rows


def build_chart_rows(company_type, legal_form):
    """Return insertion-ready tuples ``(code, parent, name_ar, name_en, kind, pack, order)``."""
    return [
        (
            row["code"], row["parent_code"], row["name_ar"], row["name_en"],
            row["kind"], row["pack"], row["sort_order"],
        )
        for row in build_chart(company_type, legal_form)
    ]


def chart_composition(company_type, legal_form):
    """Return the pack -> account codes mapping for a company (no database)."""
    composition = {PACK_BASE: [], PACK_ACTIVITY: [], PACK_LEGAL_FORM: []}
    for row in build_chart(company_type, legal_form):
        composition[row["pack"]].append(row["code"])
    return composition


def _legacy_rows(pack_name):
    """Back-compat 6-tuple rows ``(code, parent, name_ar, name_en, kind, order)``."""
    document = _validate.load_pack(pack_name)
    return tuple(
        (
            account["code"], account["parent"], account["name_ar"], account["name_en"],
            account["type"], index,
        )
        for index, account in enumerate(document["accounts"])
    )


# Back-compat data constants (old shape) derived from the JSON packs, so any
# existing reader/test that imported them keeps working unchanged.
BASE_ACCOUNTS = _legacy_rows(_validate.BASE_PACK)
ACTIVITY_ACCOUNTS = {
    activity: _legacy_rows(pack_name) for activity, pack_name in _validate.ACTIVITY_PACKS.items()
}
LEGAL_ACCOUNTS = {
    legal_form: _legacy_rows(pack_name) for legal_form, pack_name in _validate.LEGAL_FORM_PACKS.items()
}


__all__ = [
    "ACCOUNT_KINDS", "PACKS", "PACK_BASE", "PACK_ACTIVITY", "PACK_LEGAL_FORM",
    "PACK_LABELS", "KIND_LABELS", "ChartError",
    "build_chart", "build_chart_rows", "chart_composition",
]
