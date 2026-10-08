"""Provisioning-only schema runner for isolated company SQLite databases.

Application workspace reads never call the migration runner.  They use
``validate_read_only`` so an old or malformed file cannot be silently upgraded.
Read-only opens pin a verified file descriptor on POSIX, preventing a path swap
between the authorization check and SQLite opening.
"""
import os
import sqlite3
from pathlib import Path

from .company_migrations import VERSION, upgrade
from .config import COUNTRY, SCHEMA_VERSION


class CompanySchemaError(Exception):
    """A company database is absent, malformed, or at an unsupported version."""


class _PinnedConnection:
    """Small proxy that keeps the source descriptor alive for SQLite's lifetime."""
    def __init__(self, connection, fd):
        self._connection = connection
        self._fd = fd
        self._closed = False

    def execute(self, *args, **kwargs):
        return self._connection.execute(*args, **kwargs)

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._connection.close()
        finally:
            if self._fd is not None:
                try:
                    os.close(self._fd)
                finally:
                    self._fd = None

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _connect_rw(path):
    connection = sqlite3.connect(str(path), timeout=30)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def apply_migrations(path):
    """Apply all known migrations to a newly-created writable database file."""
    path = Path(path)
    connection = _connect_rw(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        upgrade(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def write_settings(path, data):
    """Write the one company settings row after schema migration."""
    connection = _connect_rw(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """INSERT INTO company_settings
               (id, name, type, legal_form, base_currency,
                fiscal_year_start_month, tax_id, currency_locked, country)
               VALUES (1, ?, ?, ?, ?, ?, ?, 0, ?)""",
            (
                data["name"], data["company_type"], data["legal_form"],
                data["base_currency"], data["fiscal_year_start_month"],
                data.get("tax_id"), COUNTRY,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def read_schema_version(connection):
    """Read only the version value; callers decide whether it is acceptable."""
    try:
        row = connection.execute("SELECT version FROM schema_meta ORDER BY version DESC LIMIT 1").fetchone()
        if not row:
            return None
        return int(row[0])
    except (sqlite3.Error, TypeError, ValueError) as exc:
        raise CompanySchemaError("Company database schema is malformed.") from exc


def validate_read_only(connection, expected_version=SCHEMA_VERSION):
    """Validate schema metadata without applying or attempting any migration."""
    try:
        version = read_schema_version(connection)
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    except CompanySchemaError:
        raise
    except (sqlite3.Error, TypeError, ValueError) as exc:
        raise CompanySchemaError("Company database could not be read.") from exc
    if version != expected_version or not {"schema_meta", "company_settings"}.issubset(tables):
        raise CompanySchemaError("Company database schema is unsupported.")
    return version


def _regular_owned_identity(path):
    """Return a pre-open identity, rejecting symlinks and foreign files."""
    try:
        info = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise CompanySchemaError("Company database is unavailable.") from exc
    if not stat_is_regular(info) or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
        raise CompanySchemaError("Company database is unavailable.")
    return info.st_dev, info.st_ino, getattr(info, "st_uid", None)


def stat_is_regular(info):
    # Avoid following the target in the pre-open check; S_ISREG works on Windows too.
    import stat
    return stat.S_ISREG(info.st_mode)


def _verify_identity(path, identity):
    try:
        info = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise CompanySchemaError("Company database is unavailable.") from exc
    current = (info.st_dev, info.st_ino, getattr(info, "st_uid", None))
    if not stat_is_regular(info) or current != identity:
        raise CompanySchemaError("Company database changed while opening.")


def open_read_only(path, validate=True):
    """Open a company file read-only, pinning its verified descriptor where possible.

    On POSIX, ``O_NOFOLLOW`` plus ``/proc/self/fd/<fd>`` prevents SQLite from
    resolving a replaced pathname.  Windows rejects symlinks/reparse-like links
    that Python exposes, and verifies identity before and after connect; Windows
    has no universal Python-level no-follow open primitive, so ACLs remain part of
    the trusted storage-directory boundary.
    """
    path = Path(path)
    connection = None
    fd = None
    identity = _regular_owned_identity(path)
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(path), flags)
        opened = os.fstat(fd)
        opened_identity = (opened.st_dev, opened.st_ino, getattr(opened, "st_uid", None))
        if not stat_is_regular(opened) or opened_identity != identity:
            raise CompanySchemaError("Company database changed while opening.")
        _verify_identity(path, identity)
        if os.name != "nt" and os.path.exists(f"/proc/self/fd/{fd}"):
            uri = f"file:/proc/self/fd/{fd}?mode=ro"
        else:
            # Windows fallback: pre/post identity checks and no symlink target.
            if path.is_symlink():
                raise CompanySchemaError("Company database is unavailable.")
            uri = path.absolute().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=30)
        _verify_identity(path, identity)
        connection.execute("PRAGMA query_only=ON")
        if validate:
            connection.execute("PRAGMA foreign_keys=ON")
            validate_read_only(connection)
        return _PinnedConnection(connection, fd)
    except CompanySchemaError:
        if connection is not None:
            connection.close()
        if fd is not None:
            os.close(fd)
        raise
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        if connection is not None:
            connection.close()
        if fd is not None:
            os.close(fd)
        raise CompanySchemaError("Company database could not be opened.") from exc


# Descriptive aliases used by callers/tests.
run_company_migrations = apply_migrations
apply_company_schema = apply_migrations
validate_schema_read_only = validate_read_only

__all__ = [
    "CompanySchemaError", "apply_migrations", "run_company_migrations",
    "apply_company_schema", "write_settings", "read_schema_version",
    "validate_read_only", "validate_schema_read_only", "open_read_only",
    "VERSION",
]
