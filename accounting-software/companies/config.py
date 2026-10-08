"""Configuration and validation constants for the per-company databases."""
from pathlib import Path

COUNTRY = "Egypt"
SCHEMA_VERSION = 1
COMPANY_TYPES = ("industrial", "contracting", "trading")
COMPANY_TYPE_LABELS = {
    "industrial": "صناعية",
    "contracting": "مقاولات",
    "trading": "تجارية",
}
LEGAL_FORMS = ("sole_proprietorship", "joint_stock")
LEGAL_FORM_LABELS = {
    "sole_proprietorship": "منشأة فردية",
    "joint_stock": "شركة مساهمة",
}
CURRENCIES = ("EGP", "USD", "EUR", "SAR", "AED")
# Alias retained as a convenient, explicit public contract.
ALLOWED_CURRENCIES = CURRENCIES
ALLOWED_COMPANY_TYPES = COMPANY_TYPES
ALLOWED_LEGAL_FORMS = LEGAL_FORMS
SUPPORTED_CURRENCIES = CURRENCIES
COMPANY_SCHEMA_VERSION = SCHEMA_VERSION
DEFAULT_COUNTRY = COUNTRY
DEFAULT_COMPANY_DATA_DIR = Path.home() / ".local" / "share" / "eid-saeed-mahmoud" / "companies"
MAX_COMPANY_NAME_LENGTH = 120
MAX_TAX_ID_LENGTH = 80

__all__ = [
    "COUNTRY", "SCHEMA_VERSION", "COMPANY_TYPES", "COMPANY_TYPE_LABELS",
    "LEGAL_FORMS", "LEGAL_FORM_LABELS", "CURRENCIES", "ALLOWED_CURRENCIES",
    "ALLOWED_COMPANY_TYPES", "ALLOWED_LEGAL_FORMS", "SUPPORTED_CURRENCIES",
    "COMPANY_SCHEMA_VERSION", "DEFAULT_COUNTRY",
    "DEFAULT_COMPANY_DATA_DIR", "MAX_COMPANY_NAME_LENGTH", "MAX_TAX_ID_LENGTH",
]
