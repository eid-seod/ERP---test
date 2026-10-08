"""Explicit Step 2 platform migration for the company registry.

This migration is intentionally not run at application startup.  Run it against
an existing, backed-up platform database, then restart the application.  A fresh
database (with no users yet) is allowed to initialize normally; its initializer
may call ``apply`` as part of its explicit fresh-schema setup.
"""
import argparse
import sqlite3
from pathlib import Path


COMPANY_DDL = (
    """CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        company_type VARCHAR(30) NOT NULL,
        legal_form VARCHAR(40) NOT NULL,
        base_currency VARCHAR(3) NOT NULL,
        fiscal_year_start_month INTEGER NOT NULL,
        tax_id VARCHAR(80),
        status VARCHAR(20) NOT NULL,
        owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        db_filename VARCHAR(160) NOT NULL UNIQUE,
        schema_version INTEGER NOT NULL,
        created_at DATETIME NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS company_memberships (
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL,
        PRIMARY KEY (user_id, company_id)
    )""",
    "CREATE INDEX IF NOT EXISTS ix_companies_status ON companies(status)",
    "CREATE INDEX IF NOT EXISTS ix_companies_company_type ON companies(company_type)",
    "CREATE INDEX IF NOT EXISTS ix_companies_owner_user_id ON companies(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS ix_company_memberships_company_id ON company_memberships(company_id)",
    "CREATE INDEX IF NOT EXISTS ix_company_memberships_user_status ON company_memberships(user_id, status)",
)

_COMPANY_COLUMNS = {
    "id": ("INTEGER", False),
    "name": ("VARCHAR(120)", True),
    "company_type": ("VARCHAR(30)", True),
    "legal_form": ("VARCHAR(40)", True),
    "base_currency": ("VARCHAR(3)", True),
    "fiscal_year_start_month": ("INTEGER", True),
    "tax_id": ("VARCHAR(80)", False),
    "status": ("VARCHAR(20)", True),
    "owner_user_id": ("INTEGER", True),
    "db_filename": ("VARCHAR(160)", True),
    "schema_version": ("INTEGER", True),
    "created_at": ("DATETIME", True),
}
_MEMBERSHIP_COLUMNS = {
    "user_id": ("INTEGER", True), "company_id": ("INTEGER", True),
    "role": ("VARCHAR(20)", True), "status": ("VARCHAR(20)", True),
}
_REQUIRED_INDEXES = {
    "ix_companies_status": ("companies", ("status",), False),
    "ix_companies_company_type": ("companies", ("company_type",), False),
    "ix_companies_owner_user_id": ("companies", ("owner_user_id",), False),
    "ix_company_memberships_company_id": ("company_memberships", ("company_id",), False),
    "ix_company_memberships_user_status": ("company_memberships", ("user_id", "status"), False),
}


def _execute(connection, sql, params=()):
    if hasattr(connection, "exec_driver_sql"):
        return connection.exec_driver_sql(sql, params)
    return connection.execute(sql, params)


def _table_names(connection):
    return {row[0] for row in _execute(connection, "SELECT name FROM sqlite_master WHERE type='table'")}


def _table_info(connection, table):
    # Table names are internal constants, never caller-controlled strings.
    return list(_execute(connection, "PRAGMA table_info(" + table + ")"))


def _columns(connection, table):
    return {row[1] for row in _table_info(connection, table)}


def _indexes(connection, table):
    return {row[1]: bool(row[2]) for row in _execute(connection, "PRAGMA index_list(" + table + ")")}


def _normalize_type(value):
    return " ".join(str(value or "").upper().split())


def _validate_columns(connection, table, expected, *, primary_key=()):
    rows = _table_info(connection, table)
    actual = {row[1]: row for row in rows}
    if not set(expected).issubset(actual):
        raise RuntimeError("Existing company registry schema is malformed; no database was changed.")
    for name, (declared_type, required) in expected.items():
        row = actual[name]
        # SQLite table_info: cid, name, type, notnull, dflt_value, pk.
        # SQLite reports INTEGER PRIMARY KEY as nullable in raw DDL, while
        # SQLAlchemy may emit an explicit NOT NULL.  Either is valid for a PK;
        # nullability remains strict for all non-key columns.
        if _normalize_type(row[2]) != declared_type or (not row[5] and bool(row[3]) != required):
            raise RuntimeError("Existing company registry schema is malformed; no database was changed.")
    if tuple(row[1] for row in sorted(rows, key=lambda item: item[5]) if row[5]) != tuple(primary_key):
        raise RuntimeError("Existing company registry primary key is malformed; no database was changed.")


def _foreign_keys(connection, table):
    return list(_execute(connection, "PRAGMA foreign_key_list(" + table + ")"))


def _require_foreign_key(connection, table, source, target_table, target_column, on_delete):
    for row in _foreign_keys(connection, table):
        # id, seq, table, from, to, on_update, on_delete, match
        if row[3] == source and row[2] == target_table and row[4] == target_column and row[6].upper() == on_delete:
            return
    raise RuntimeError("Existing company registry foreign keys are malformed; no database was changed.")


def _index_columns(connection, table, index_name):
    return tuple(row[2] for row in _execute(connection, "PRAGMA index_info(" + index_name + ")"))


def _require_indexes(connection):
    for name, (table, columns, unique) in _REQUIRED_INDEXES.items():
        rows = {row[1]: bool(row[2]) for row in _execute(connection, "PRAGMA index_list(" + table + ")")}
        if name not in rows or rows[name] != unique or _index_columns(connection, table, name) != columns:
            raise RuntimeError("Existing company registry indexes are malformed; no database was changed.")
    # db_filename uniqueness may be an inline UNIQUE auto-index or a named index.
    unique_ok = False
    for index_name, is_unique in {row[1]: bool(row[2]) for row in _execute(connection, "PRAGMA index_list(companies)")}.items():
        if is_unique and _index_columns(connection, "companies", index_name) == ("db_filename",):
            unique_ok = True
            break
    if not unique_ok:
        raise RuntimeError("Existing company registry uniqueness is malformed; no database was changed.")


def _validate_registry(connection, tables):
    if not {"companies", "company_memberships"}.issubset(tables):
        raise RuntimeError("Existing database requires the explicit Step 2 migration: migrations/companies.py.")
    _validate_columns(connection, "companies", _COMPANY_COLUMNS, primary_key=("id",))
    _validate_columns(connection, "company_memberships", _MEMBERSHIP_COLUMNS, primary_key=("user_id", "company_id"))
    _require_foreign_key(connection, "companies", "owner_user_id", "users", "id", "RESTRICT")
    _require_foreign_key(connection, "company_memberships", "user_id", "users", "id", "CASCADE")
    _require_foreign_key(connection, "company_memberships", "company_id", "companies", "id", "CASCADE")
    _require_indexes(connection)


def _require_step1(connection, tables, users):
    required_users = {
        "id", "email", "role", "is_active", "password_hash",
        "deleted_at", "last_login_at", "session_epoch",
    }
    if not required_users.issubset(users):
        raise RuntimeError("Step 1 migration is required before Step 2; no database was changed.")
    if not {"user_audit_events", "platform_settings"}.issubset(tables):
        raise RuntimeError("Step 1 migration is required before Step 2; no database was changed.")
    if not _indexes(connection, "users").get("ux_users_email_normalized"):
        raise RuntimeError("Step 1 normalized email index is required before Step 2; no database was changed.")


def _validate_platform_settings(connection):
    expected = {"key": ("VARCHAR(80)", False), "value": ("BOOLEAN", True), "updated_at": ("DATETIME", True)}
    rows = _table_info(connection, "platform_settings")
    actual = {row[1]: row for row in rows}
    if not set(expected).issubset(actual):
        raise RuntimeError("Existing platform settings schema is malformed; no database was changed.")
    for name, (declared_type, required) in expected.items():
        if _normalize_type(actual[name][2]) != declared_type or (not actual[name][5] and bool(actual[name][3]) != required):
            raise RuntimeError("Existing platform settings schema is malformed; no database was changed.")
    pk = tuple(row[1] for row in sorted(rows, key=lambda item: item[5]) if row[5])
    if pk != ("key",):
        raise RuntimeError("Existing platform settings schema is malformed; no database was changed.")
    if "integer_value" in actual and (_normalize_type(actual["integer_value"][2]) != "INTEGER" or bool(actual["integer_value"][3])):
        raise RuntimeError("Existing platform settings schema is malformed; no database was changed.")


def _validate_max_setting(connection, *, require_present=False):
    row = _execute(
        connection,
        "SELECT integer_value FROM platform_settings WHERE key='max_companies_per_user' LIMIT 1",
    ).fetchone()
    if row is None:
        if require_present:
            raise RuntimeError("Existing max-companies setting is invalid; no database was changed.")
        return False
    value = row[0]
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise RuntimeError("Existing max-companies setting is invalid; no database was changed.")
    return True


def apply(connection):
    """Apply Step 2 to an already Step 1-compatible platform connection."""
    tables = _table_names(connection)
    users = _columns(connection, "users") if "users" in tables else set()
    _require_step1(connection, tables, users)
    if list(_execute(connection, "SELECT lower(email) FROM users GROUP BY lower(email) HAVING count(*) > 1")):
        raise RuntimeError("Existing case-insensitive duplicate emails require owner review; no database was changed.")
    _validate_platform_settings(connection)
    existing_registry = bool({"companies", "company_memberships"} & tables)
    if existing_registry:
        # Validate every pre-existing registry artifact before any ALTER/INSERT.
        _validate_registry(connection, tables)
        if "integer_value" in _columns(connection, "platform_settings"):
            _validate_max_setting(connection, require_present=False)
        else:
            # An already-present row has no trustworthy numeric value to
            # migrate; do not add a column before rejecting it.
            if _execute(connection, "SELECT 1 FROM platform_settings WHERE key='max_companies_per_user' LIMIT 1").fetchone():
                raise RuntimeError("Existing max-companies setting is invalid; no database was changed.")
    elif "integer_value" in _columns(connection, "platform_settings"):
        _validate_max_setting(connection, require_present=False)
    elif _execute(connection, "SELECT 1 FROM platform_settings WHERE key='max_companies_per_user' LIMIT 1").fetchone():
        raise RuntimeError("Existing max-companies setting is invalid; no database was changed.")
    if "integer_value" not in _columns(connection, "platform_settings"):
        _execute(connection, "ALTER TABLE platform_settings ADD COLUMN integer_value INTEGER")
    if existing_registry:
        # An existing max row must not be silently repaired or overwritten.
        _validate_max_setting(connection, require_present=False)
    for statement in COMPANY_DDL:
        _execute(connection, statement)
    if not _validate_max_setting(connection, require_present=False):
        _execute(
            connection,
            """INSERT INTO platform_settings(key, value, integer_value, updated_at)
               VALUES ('max_companies_per_user', 0, 1, CURRENT_TIMESTAMP)""",
        )
    # Creation is followed by the same strict verification used for pre-existing tables.
    _validate_registry(connection, _table_names(connection))
    _validate_max_setting(connection, require_present=True)


def require_existing_company_upgrade(engine):
    """Reject an existing populated platform DB missing any Step 2 artifact.

    This startup preflight never writes.  A genuinely fresh database has no users
    table yet and is returned unchanged; an existing users table requires the
    explicit migration and a fully valid company registry.
    """
    with engine.connect() as connection:
        tables = _table_names(connection)
        if "users" not in tables:
            return
        _require_step1(connection, tables, _columns(connection, "users"))
        _validate_platform_settings(connection)
        if "integer_value" not in _columns(connection, "platform_settings"):
            raise RuntimeError("Existing database requires the explicit Step 2 migration: migrations/companies.py.")
        if not {"companies", "company_memberships"}.issubset(tables):
            raise RuntimeError("Existing database requires the explicit Step 2 migration: migrations/companies.py.")
        _validate_registry(connection, tables)
        _validate_max_setting(connection, require_present=True)


def migrate_file(path):
    """Run the migration on an existing SQLite file without creating one."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError("Existing database file is required. Refusing to create one.")
    with sqlite3.connect(path.as_uri() + "?mode=rw", uri=True) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        try:
            apply(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise


# Parent startup code may use the shorter Step 1-style preflight name.
require_existing_upgrade = require_existing_company_upgrade


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply the explicit Step 2 company registry migration.")
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    migrate_file(args.database)
    print("Step 2 company migration applied. Existing users/settings were preserved.")
