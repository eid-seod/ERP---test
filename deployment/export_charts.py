"""Generate a human-review chart-of-accounts document from the JSON packs.

Produces ``docs/chart-of-accounts-review.md`` with one indented table per
composition (the six activity x legal-form combinations).  Each row shows the
account code, Arabic name, English name, type, postable flag and system flag.
Standard library only; reads the packs through the shared composer.

    python deployment/export_charts.py
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"
if str(PACKS) not in sys.path:
    sys.path.insert(0, str(PACKS))

import compose  # noqa: E402  (packs/compose.py)

OUTPUT = ROOT / "docs" / "chart-of-accounts-review.md"

ACTIVITY_LABELS = {
    "industrial": "صناعية — Industrial",
    "contracting": "مقاولات — Contracting",
    "trading": "تجارية — Trading",
}
LEGAL_LABELS = {
    "sole_proprietorship": "منشأة فردية — Sole proprietorship",
    "joint_stock": "شركة مساهمة — Joint stock",
}


def _render_table(rows):
    lines = [
        "| Code | Name (AR) | Name (EN) | Type | Postable | System |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        indent = "" if row["parent"] is None else "&nbsp;&nbsp;&nbsp;&nbsp;"
        # Extra indent for grandchildren keeps the hierarchy readable in tables.
        if row["parent"] and row["parent"] not in (None, "1000", "2000", "3000", "4000", "5000", "6000", "7000"):
            indent += "&nbsp;&nbsp;&nbsp;&nbsp;"
        lines.append(
            "| `{code}` | {indent}{ar} | {en} | {type} | {postable} | {system} |".format(
                code=row["code"], indent=indent, ar=row["name_ar"], en=row["name_en"],
                type=row["type"], postable="yes" if row["is_postable"] else "—",
                system="yes" if row["is_system"] else "—",
            )
        )
    return "\n".join(lines)


def build_document():
    import validate as _validate

    validate_result = _validate.validate_packs()
    versions = {name: pack["version"] for name, pack in validate_result["packs"].items()}
    lines = [
        "# Chart of accounts — review export",
        "",
        "Generated from the versioned JSON packs in `packs/` (data + validator only).",
        "A company chart is composed as **base + exactly one activity + exactly one "
        "legal-form layer**; it is never six separate charts.",
        "",
        "Generated on {today}. Pack versions: {versions}.".format(
            today=date.today().isoformat(),
            versions=", ".join(f"`{name}` {version}" for name, version in sorted(versions.items())),
        ),
        "",
    ]
    for activity in compose.ACTIVITY_TYPES:
        for legal_form in compose.LEGAL_FORMS:
            rows = compose.compose_chart(activity, legal_form)
            lines.append(f"## {ACTIVITY_LABELS[activity]} · {LEGAL_LABELS[legal_form]}")
            lines.append("")
            lines.append(f"_{len(rows)} accounts._")
            lines.append("")
            lines.append(_render_table(rows))
            lines.append("")
    return "\n".join(lines)


def main():
    document = build_document()
    OUTPUT.write_text(document, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(document)} bytes).")


if __name__ == "__main__":
    main()
