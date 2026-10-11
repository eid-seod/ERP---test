"""Validate the versioned JSON account packs (standard library only).

Design notes
------------
* A composition always combines **base + exactly one activity + exactly one
  legal-form layer**.  Two activity packs never combine, and two legal-form
  layers never combine.  Therefore account codes must be unique *within* each
  pack and *disjoint between every pair of packs that can co-occur*:
  base/activity, base/legal-form and activity/legal-form.  Codes may repeat
  across packs that never co-occur (e.g. the equity group header ``3000`` is
  defined by each legal-form layer).
* Structural rules (every parent exists, a child's ``type`` equals its parent's
  ``type``, and postable accounts are always leaves) are checked **per
  composition**, because a group header in the base pack only receives children
  from the selected activity/legal-form layer.

Run directly to validate every pack and all six compositions:

    python packs/validate.py
"""
import argparse
import json
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parent

BASE_PACK = "base.json"
ACTIVITY_PACKS = {
    "trading": "trading.json",
    "industrial": "industrial.json",
    "contracting": "contracting.json",
}
LEGAL_FORM_PACKS = {
    "sole_proprietorship": "legal_form_sole_proprietorship.json",
    "joint_stock": "legal_form_joint_stock.json",
}

PACK_NAMES = (BASE_PACK, *ACTIVITY_PACKS.values(), *LEGAL_FORM_PACKS.values())

REQUIRED_FIELDS = (
    "code", "name_ar", "name_en", "type", "parent",
    "is_postable", "is_system", "normal_balance", "description",
)

ACCOUNT_TYPES = ("asset", "liability", "equity", "revenue", "expense")
NORMAL_BALANCES = ("debit", "credit")

# First digit -> allowed account types (the Step 3A numbering decision):
# 1 assets, 2 liabilities, 3 equity, 4 revenue, 5 cost of sales/direct costs,
# 6 operating expenses, 7 other income/expenses.
NUMBERING = {
    "1": ("asset",),
    "2": ("liability",),
    "3": ("equity",),
    "4": ("revenue",),
    "5": ("expense",),
    "6": ("expense",),
    "7": ("revenue", "expense"),
}


class PackError(Exception):
    """A pack is missing, malformed, or inconsistent with the catalog."""


def pack_path(name, pack_dir=PACK_DIR):
    return Path(pack_dir) / name


def load_pack(name, pack_dir=PACK_DIR):
    """Load one pack document, validating its envelope only."""
    path = pack_path(name, pack_dir)
    if not path.is_file():
        raise PackError(f"Missing pack file: {name}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PackError(f"Pack {name} is not valid JSON.") from exc
    if not isinstance(document, dict):
        raise PackError(f"Pack {name} must be a JSON object.")
    version = document.get("version")
    if not isinstance(version, str) or not version.strip():
        raise PackError(f"Pack {name} requires a string 'version'.")
    accounts = document.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise PackError(f"Pack {name} requires a non-empty 'accounts' list.")
    return {"version": version, "accounts": accounts}


def _validate_account(account, name, index):
    if not isinstance(account, dict):
        raise PackError(f"Pack {name} account #{index} must be an object.")
    for field in REQUIRED_FIELDS:
        if field not in account:
            raise PackError(f"Pack {name} account #{index} is missing '{field}'.")
    code = account["code"]
    if not isinstance(code, str) or not code or not code.isdigit():
        raise PackError(f"Pack {name} account #{index} has an invalid code.")
    for field in ("name_ar", "name_en"):
        if not isinstance(account[field], str) or not account[field].strip():
            raise PackError(f"Pack {name} account {code} requires a non-empty {field}.")
    if account["type"] not in ACCOUNT_TYPES:
        raise PackError(f"Pack {name} account {code} has an invalid type.")
    parent = account["parent"]
    if parent is not None and (not isinstance(parent, str) or not parent or not parent.isdigit()):
        raise PackError(f"Pack {name} account {code} has an invalid parent.")
    for field in ("is_postable", "is_system"):
        if not isinstance(account[field], bool):
            raise PackError(f"Pack {name} account {code} requires boolean {field}.")
    if account["normal_balance"] not in NORMAL_BALANCES:
        raise PackError(f"Pack {name} account {code} has an invalid normal_balance.")
    if not isinstance(account["description"], str):
        raise PackError(f"Pack {name} account {code} requires a string description.")
    allowed = NUMBERING.get(code[0])
    if not allowed or account["type"] not in allowed:
        raise PackError(
            f"Pack {name} account {code} type '{account['type']}' does not match its "
            f"numbering group '{code[0]}'."
        )
    return account


def _validate_pack(name, pack_dir):
    """Validate one pack in isolation; return ``{code: account}``."""
    document = load_pack(name, pack_dir)
    by_code = {}
    for index, account in enumerate(document["accounts"]):
        account = _validate_account(account, name, index)
        code = account["code"]
        if code in by_code:
            raise PackError(f"Pack {name} has duplicate account code {code}.")
        by_code[code] = account
    return {"version": document["version"], "accounts": by_code}


def _validate_composition(activity, legal_form, base, activity_accounts, legal_accounts):
    """Validate parents/types/postable-leaves over one concrete composition."""
    merged = dict(base)
    merged.update(activity_accounts)
    merged.update(legal_accounts)
    children = {}
    for code, account in merged.items():
        parent = account["parent"]
        if parent is None:
            continue
        if parent not in merged:
            raise PackError(
                f"Composition {activity}/{legal_form}: account {code} references "
                f"missing parent {parent}."
            )
        if merged[parent]["type"] != account["type"]:
            raise PackError(
                f"Composition {activity}/{legal_form}: account {code} type "
                f"'{account['type']}' differs from parent {parent} type "
                f"'{merged[parent]['type']}'."
            )
        children.setdefault(parent, []).append(code)
    for code, account in merged.items():
        if code in children and account["is_postable"]:
            raise PackError(
                f"Composition {activity}/{legal_form}: postable account {code} must be "
                f"a leaf but has children."
            )
    return merged


def validate_packs(pack_dir=PACK_DIR):
    """Validate every pack and all six compositions.  Returns a summary dict."""
    packs = {name: _validate_pack(name, pack_dir) for name in PACK_NAMES}
    base = packs[BASE_PACK]["accounts"]

    # Disjointness for every pair of packs that can co-occur.
    for activity_name, activity_pack in ACTIVITY_PACKS.items():
        activity = packs[activity_pack]["accounts"]
        overlap = set(base) & set(activity)
        if overlap:
            raise PackError(f"Base and {activity_name} packs share codes: {sorted(overlap)}")
        for legal_form, legal_pack in LEGAL_FORM_PACKS.items():
            legal = packs[legal_pack]["accounts"]
            overlap = set(activity) & set(legal)
            if overlap:
                raise PackError(f"{activity_name} and {legal_form} packs share codes: {sorted(overlap)}")
    for legal_pack in LEGAL_FORM_PACKS.values():
        overlap = set(base) & set(packs[legal_pack]["accounts"])
        if overlap:
            raise PackError(f"Base and {legal_pack} share codes: {sorted(overlap)}")

    compositions = {}
    for activity, activity_pack in ACTIVITY_PACKS.items():
        for legal_form, legal_pack in LEGAL_FORM_PACKS.items():
            merged = _validate_composition(
                activity, legal_form, base,
                packs[activity_pack]["accounts"], packs[legal_pack]["accounts"],
            )
            compositions[(activity, legal_form)] = merged
    return {"packs": packs, "compositions": compositions}


# Alias kept for callers/tests.
def validate_catalog(pack_dir=PACK_DIR):
    return validate_packs(pack_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate the JSON account packs.")
    parser.add_argument("--packs", default=str(PACK_DIR), help="Directory containing the packs.")
    arguments = parser.parse_args()
    result = validate_packs(Path(arguments.packs))
    total = sum(len(pack["accounts"]) for pack in result["packs"].values())
    print(
        "OK: {packs} packs, {total} accounts total, {comps} compositions validated.".format(
            packs=len(result["packs"]), total=total, comps=len(result["compositions"])
        )
    )
