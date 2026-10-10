"""Bilingual chart-of-accounts catalog and pack composition.

One company chart is *composed*, never authored as a separate per-company chart:

* a **base pack** shared by every company,
* exactly one **activity pack** chosen from the company type, and
* exactly one **legal-form layer** chosen from the legal form.

Account names are bilingual: Arabic is the primary (displayed) name and English
is the secondary name, matching the accepted Step 3 decisions.  The catalog is a
pure, dependency-free module so it can be validated and unit-tested without a
database.
"""

from .config import COMPANY_TYPES, LEGAL_FORMS

# Account kinds.  Codes are grouped by kind (1 assets, 2 liabilities, 3 equity,
# 4 revenue, 5 expenses) so a composed chart stays human-readable.
ACCOUNT_KINDS = ("asset", "liability", "equity", "revenue", "expense")

PACK_BASE = "base"
PACK_ACTIVITY = "activity"
PACK_LEGAL_FORM = "legal_form"
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

# ``(code, parent_code, name_ar, name_en, kind, sort_order)``
BASE_ACCOUNTS = (
    ("1000", None, "الأصول", "Assets", "asset", 10),
    ("1100", "1000", "الأصول المتداولة", "Current assets", "asset", 11),
    ("1110", "1100", "النقدية بالصندوق", "Cash on hand", "asset", 12),
    ("1120", "1100", "النقدية بالبنوك", "Cash at bank", "asset", 13),
    ("1200", "1000", "الأصول غير المتداولة", "Non-current assets", "asset", 14),
    ("1210", "1200", "الأصول الثابتة", "Property, plant and equipment", "asset", 15),
    ("2000", None, "الالتزامات", "Liabilities", "liability", 20),
    ("2100", "2000", "الالتزامات المتداولة", "Current liabilities", "liability", 21),
    ("2110", "2100", "الموردون", "Accounts payable", "liability", 22),
    ("2120", "2100", "مصروفات مستحقة", "Accrued expenses", "liability", 23),
    ("2200", "2000", "الالتزامات غير المتداولة", "Non-current liabilities", "liability", 24),
    ("2210", "2200", "قروض طويلة الأجل", "Long-term loans", "liability", 25),
    ("3000", None, "حقوق الملكية", "Equity", "equity", 30),
    ("3100", "3000", "رأس المال", "Capital", "equity", 31),
    ("3200", "3000", "الأرباح المحتجزة", "Retained earnings", "equity", 32),
    ("4000", None, "الإيرادات", "Revenue", "revenue", 40),
    ("4100", "4000", "إيرادات المبيعات", "Sales revenue", "revenue", 41),
    ("5000", None, "المصروفات", "Expenses", "expense", 50),
    ("5900", "5000", "مصروفات إدارية وعمومية", "General and administrative expenses", "expense", 51),
)

ACTIVITY_ACCOUNTS = {
    "industrial": (
        ("1300", "1100", "مخزون المواد الخام", "Raw materials inventory", "asset", 16),
        ("1310", "1100", "مخزون المنتجات التامة", "Finished goods inventory", "asset", 17),
        ("4110", "4000", "إيرادات بيع الإنتاج", "Revenue from manufactured goods", "revenue", 42),
        ("5100", "5000", "تكلفة المبيعات", "Cost of goods sold", "expense", 52),
        ("5200", "5000", "تكاليف صناعية غير مباشرة", "Manufacturing overhead", "expense", 53),
    ),
    "contracting": (
        ("1400", "1100", "أعمال تحت التنفيذ", "Contract work in progress", "asset", 16),
        ("4120", "4000", "إيرادات المقاولات", "Contract revenue", "revenue", 42),
        ("5300", "5000", "تكاليف المشروعات المباشرة", "Project direct costs", "expense", 52),
    ),
    "trading": (
        ("1500", "1100", "مخزون البضاعة", "Merchandise inventory", "asset", 16),
        ("4130", "4000", "إيرادات بيع البضاعة", "Revenue from traded goods", "revenue", 42),
        ("5400", "5000", "تكلفة المبيعات", "Cost of goods sold", "expense", 52),
    ),
}

LEGAL_ACCOUNTS = {
    "sole_proprietorship": (
        ("3110", "3000", "مسحوبات المالك", "Owner's drawings", "equity", 33),
    ),
    "joint_stock": (
        ("3120", "3000", "الاحتياطي القانوني", "Legal reserve", "equity", 33),
        ("2130", "2100", "توزيعات أرباح مستحقة الدفع", "Dividends payable", "liability", 26),
    ),
}


class ChartError(Exception):
    """A chart could not be composed from the supplied type/legal form."""


def _validate_pack(accounts, pack, known_codes):
    for account in accounts:
        code, parent, name_ar, name_en, kind, order = account
        if len(account) != 6:
            raise ChartError(f"Account entry for pack {pack} must have six fields.")
        if not isinstance(code, str) or not code:
            raise ChartError(f"Account code in pack {pack} is invalid.")
        if code in known_codes:
            raise ChartError(f"Duplicate account code {code} in pack {pack}.")
        if kind not in ACCOUNT_KINDS:
            raise ChartError(f"Account {code} has an invalid kind.")
        if not isinstance(name_ar, str) or not name_ar.strip():
            raise ChartError(f"Account {code} requires an Arabic primary name.")
        if not isinstance(name_en, str) or not name_en.strip():
            raise ChartError(f"Account {code} requires an English secondary name.")
        if not isinstance(order, int) or isinstance(order, bool):
            raise ChartError(f"Account {code} has an invalid sort order.")
        known_codes.add(code)
    # Parent references may point at a code defined in any composed layer.
    for code, parent, *_ in accounts:
        if parent is not None and not isinstance(parent, str):
            raise ChartError(f"Account {code} has an invalid parent.")


def build_chart(company_type, legal_form):
    """Compose the three-layer chart for one company.

    Returns a list of dicts sorted by ``sort_order`` then ``code``.  ``pack``
    records which layer contributed each account so the composition is explicit.
    """
    if company_type not in COMPANY_TYPES:
        raise ChartError("A valid company type is required to build the chart.")
    if legal_form not in LEGAL_FORMS:
        raise ChartError("A valid legal form is required to build the chart.")

    known_codes = set()
    _validate_pack(BASE_ACCOUNTS, PACK_BASE, known_codes)
    _validate_pack(ACTIVITY_ACCOUNTS[company_type], PACK_ACTIVITY, known_codes)
    _validate_pack(LEGAL_ACCOUNTS[legal_form], PACK_LEGAL_FORM, known_codes)

    rows = []
    for pack, accounts in (
        (PACK_BASE, BASE_ACCOUNTS),
        (PACK_ACTIVITY, ACTIVITY_ACCOUNTS[company_type]),
        (PACK_LEGAL_FORM, LEGAL_ACCOUNTS[legal_form]),
    ):
        for code, parent, name_ar, name_en, kind, order in accounts:
            rows.append(
                {
                    "code": code,
                    "parent_code": parent,
                    "name_ar": name_ar,
                    "name_en": name_en,
                    "kind": kind,
                    "pack": pack,
                    "sort_order": order,
                }
            )
    rows.sort(key=lambda row: (row["sort_order"], row["code"]))
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


__all__ = [
    "ACCOUNT_KINDS", "PACKS", "PACK_BASE", "PACK_ACTIVITY", "PACK_LEGAL_FORM",
    "BASE_ACCOUNTS", "ACTIVITY_ACCOUNTS", "LEGAL_ACCOUNTS", "ChartError",
    "build_chart", "build_chart_rows", "chart_composition",
]
