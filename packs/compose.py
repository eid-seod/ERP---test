"""Compose a company chart from JSON packs (standard library only).

A company chart is the ordered composition of:

* the **base pack** (shared),
* exactly one **activity pack** (by company type), and
* exactly one **legal-form layer** (by legal form).

Composition is deterministic: it validates the whole catalog, then emits the
selected accounts sorted by ``(code, pack_rank)``.  ``compose_chart`` never
touches a database.
"""
import argparse
import json
from pathlib import Path

try:  # loaded as a top-level module (companies.chart_config adds this dir to sys.path)
    from validate import (
        ACTIVITY_PACKS, BASE_PACK, LEGAL_FORM_PACKS, PACK_DIR, PackError,
        load_pack, validate_packs,
    )
except ImportError:  # imported as the ``packs.compose`` package module
    from .validate import (  # type: ignore
        ACTIVITY_PACKS, BASE_PACK, LEGAL_FORM_PACKS, PACK_DIR, PackError,
        load_pack, validate_packs,
    )

# Which layer contributed an account (recorded on each composed row).
LAYER_BASE = "base"
LAYER_ACTIVITY = "activity"
LAYER_LEGAL_FORM = "legal_form"

_LAYER_RANK = {LAYER_BASE: 0, LAYER_ACTIVITY: 1, LAYER_LEGAL_FORM: 2}

ACTIVITY_TYPES = ("industrial", "contracting", "trading")
LEGAL_FORMS = ("sole_proprietorship", "joint_stock")


class ComposeError(PackError):
    """A chart could not be composed from the supplied activity/legal form."""


def _load_layers(activity, legal_form, pack_dir):
    if activity not in ACTIVITY_PACKS:
        raise ComposeError("A valid company activity is required to compose the chart.")
    if legal_form not in LEGAL_FORM_PACKS:
        raise ComposeError("A valid legal form is required to compose the chart.")
    validate_packs(pack_dir)
    return (
        (LAYER_BASE, load_pack(BASE_PACK, pack_dir)["accounts"]),
        (LAYER_ACTIVITY, load_pack(ACTIVITY_PACKS[activity], pack_dir)["accounts"]),
        (LAYER_LEGAL_FORM, load_pack(LEGAL_FORM_PACKS[legal_form], pack_dir)["accounts"]),
    )


def compose_chart(activity, legal_form, pack_dir=PACK_DIR):
    """Return the deterministic, sorted composed chart for a company.

    Each row is a dict with the pack account fields plus ``layer`` (which pack
    contributed it) and ``pack_version`` (that pack's declared version).
    """
    layers = _load_layers(activity, legal_form, pack_dir)
    versions = {
        LAYER_BASE: load_pack(BASE_PACK, pack_dir)["version"],
        LAYER_ACTIVITY: load_pack(ACTIVITY_PACKS[activity], pack_dir)["version"],
        LAYER_LEGAL_FORM: load_pack(LEGAL_FORM_PACKS[legal_form], pack_dir)["version"],
    }
    rows = []
    for layer, accounts in layers:
        for account in accounts:
            row = dict(account)
            row["layer"] = layer
            row["pack_version"] = versions[layer]
            rows.append(row)
    rows.sort(key=lambda row: (row["code"], _LAYER_RANK[row["layer"]]))
    return rows


def compose_chart_sorted(activity, legal_form, pack_dir=PACK_DIR):
    """Alias that emphasizes the deterministic ordering guarantee."""
    return compose_chart(activity, legal_form, pack_dir)


def composition(activity, legal_form, pack_dir=PACK_DIR):
    """Return ``{layer: [codes...]}`` for a composed chart."""
    result = {LAYER_BASE: [], LAYER_ACTIVITY: [], LAYER_LEGAL_FORM: []}
    for row in compose_chart(activity, legal_form, pack_dir):
        result[row["layer"]].append(row["code"])
    return result


def all_compositions(pack_dir=PACK_DIR):
    """Return the six composed charts keyed by ``(activity, legal_form)``."""
    return {
        (activity, legal_form): compose_chart(activity, legal_form, pack_dir)
        for activity in ACTIVITY_TYPES
        for legal_form in LEGAL_FORMS
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compose and print a chart of accounts.")
    parser.add_argument("activity", choices=ACTIVITY_TYPES)
    parser.add_argument("legal_form", choices=LEGAL_FORMS)
    parser.add_argument("--packs", default=str(PACK_DIR))
    arguments = parser.parse_args()
    for row in compose_chart(arguments.activity, arguments.legal_form, Path(arguments.packs)):
        print(json.dumps(row, ensure_ascii=False))
