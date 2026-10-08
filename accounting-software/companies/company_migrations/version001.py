"""Version 001 for a newly provisioned company database.

Only the two tables in this module are part of the initial company workspace.
The migration is intentionally separate from the platform database migration.
"""
from datetime import datetime, timezone

VERSION = 1


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")


def upgrade(connection):
    """Create the version history and singleton settings tables, idempotently."""
    connection.execute(
        """CREATE TABLE IF NOT EXISTS schema_meta (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME NOT NULL
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS company_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name VARCHAR(120) NOT NULL,
            type VARCHAR(30) NOT NULL,
            legal_form VARCHAR(40) NOT NULL,
            base_currency VARCHAR(3) NOT NULL,
            fiscal_year_start_month INTEGER NOT NULL,
            tax_id VARCHAR(80),
            currency_locked INTEGER NOT NULL DEFAULT 0 CHECK (currency_locked IN (0, 1)),
            country VARCHAR(80) NOT NULL DEFAULT 'Egypt'
        )"""
    )
    connection.execute(
        "INSERT OR IGNORE INTO schema_meta(version, applied_at) VALUES (?, ?)",
        (VERSION, _now()),
    )


def downgrade(connection):
    """Present for migration tooling; normal provisioning never downgrades."""
    connection.execute("DROP TABLE IF EXISTS company_settings")
    connection.execute("DROP TABLE IF EXISTS schema_meta")


__all__ = ["VERSION", "upgrade", "downgrade"]
