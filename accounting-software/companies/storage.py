"""Company registry and isolated SQLite storage services.

The platform SQLAlchemy session is used only for registry/auth/audit metadata.
The only regular workspace database opener is :func:`open_company_database`;
callers receive a query-only SQLite connection after membership validation.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
import uuid
from collections.abc import Mapping

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_session
from models.user import User
from super_admin.models import PlatformSetting
from super_admin.service import AdminError, audit

from .company_schema import CompanySchemaError, apply_migrations, open_read_only, read_schema_version, write_settings
from .config import (
    COMPANY_TYPES, CURRENCIES, DEFAULT_COMPANY_DATA_DIR, LEGAL_FORMS,
    MAX_COMPANY_NAME_LENGTH, MAX_TAX_ID_LENGTH, SCHEMA_VERSION,
)
from .models import Company, CompanyMembership, utcnow


class CompanyError(Exception):
    """Safe, user-facing company service error; never includes paths or SQL."""
    def __init__(self, message, status=400, code="company_error"):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code

    def __str__(self):
        return self.message


def _safe_error(code="provision_failed", status=500):
    return CompanyError("Company setup could not be completed. Please try again.", status, code)


def _app_config(name, default=None):
    try:
        from flask import current_app, has_app_context
        if has_app_context() and name in current_app.config:
            return current_app.config[name]
    except Exception:
        pass
    return default


def company_data_dir():
    """Return the configured company directory, creating it if necessary."""
    configured = _app_config("COMPANY_DATA_DIR")
    if configured is None:
        configured = os.environ.get("COMPANY_DATA_DIR")
    base = Path(configured).expanduser() if configured else DEFAULT_COMPANY_DATA_DIR
    try:
        # Do not accept a configured root which is itself a symlink.  Resolve
        # only after that check so a normal absolute path is stable for callers.
        if base.exists() and base.is_symlink():
            raise OSError(errno.ELOOP, "symlinked company root")
        base = base.absolute()
        base.mkdir(parents=True, exist_ok=True)
        info = os.stat(base, follow_symlinks=False)
        if not os.path.isdir(base) or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
            raise OSError(errno.EACCES, "company root ownership")
        if os.name != "nt":
            if info.st_mode & 0o077:
                os.chmod(base, 0o700)
                info = os.stat(base, follow_symlinks=False)
            if info.st_mode & 0o077:
                raise OSError(errno.EACCES, "company root permissions")
    except OSError as exc:
        raise CompanyError("Company storage is unavailable.", 503, "storage_unavailable") from exc
    return base


def _safe_generated_path(base, filename):
    """Resolve a registry filename and reject absolute/traversal/symlink paths."""
    if not isinstance(filename, str) or "\\" in filename or not re.fullmatch(
        r"company-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\.db",
        filename,
    ):
        raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
    candidate = Path(filename)
    if candidate.is_absolute() or candidate.name != filename or filename in {"", ".", ".."}:
        raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
    try:
        resolved = base / candidate
        if os.path.commonpath((str(base), str(resolved))) != str(base):
            raise ValueError
    except (ValueError, OSError) as exc:
        raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path") from exc
    if (base / candidate).is_symlink():
        raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
    return resolved


def _generated_filename():
    return "company-" + str(uuid.uuid4()) + ".db"


def _hook(stage):
    hook = _app_config("COMPANY_PROVISION_HOOK")
    if callable(hook):
        hook(stage)


def _validate_data(data):
    if not isinstance(data, Mapping):
        raise CompanyError("Enter valid company details.", 400, "invalid_data")
    name = data.get("name")
    company_type = data.get("company_type")
    legal_form = data.get("legal_form")
    currency = data.get("base_currency")
    month = data.get("fiscal_year_start_month")
    tax_id = data.get("tax_id")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > MAX_COMPANY_NAME_LENGTH:
        raise CompanyError("Company name is required and must be 120 characters or fewer.", 400, "invalid_name")
    if not isinstance(company_type, str) or company_type not in COMPANY_TYPES:
        raise CompanyError("Choose a valid company type.", 400, "invalid_company_type")
    if not isinstance(legal_form, str) or legal_form not in LEGAL_FORMS:
        raise CompanyError("Choose a valid legal form.", 400, "invalid_legal_form")
    if not isinstance(currency, str) or currency not in CURRENCIES:
        raise CompanyError("Choose a valid base currency.", 400, "invalid_currency")
    if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
        raise CompanyError("Fiscal year start month must be between 1 and 12.", 400, "invalid_fiscal_month")
    if tax_id is not None and not isinstance(tax_id, str):
        raise CompanyError("Tax ID is invalid.", 400, "invalid_tax_id")
    tax_id = tax_id.strip() if isinstance(tax_id, str) else None
    if tax_id == "":
        tax_id = None
    if tax_id is not None and len(tax_id) > MAX_TAX_ID_LENGTH:
        raise CompanyError("Tax ID is too long.", 400, "invalid_tax_id")
    return {
        "name": name.strip(), "company_type": company_type, "legal_form": legal_form,
        "base_currency": currency, "fiscal_year_start_month": month, "tax_id": tax_id,
    }


def _actor_in_transaction(db, actor_id, expected_epoch=None, standard_only=True):
    actor = db.get(User, actor_id)
    if not actor or not actor.is_active or actor.deleted_at or (standard_only and actor.role != "user"):
        raise CompanyError("Authentication required.", 403, "actor_not_allowed")
    if expected_epoch is not None and actor.session_epoch != expected_epoch:
        raise CompanyError("Authentication required.", 403, "session_expired")
    return actor


def _max_companies(db):
    try:
        row = db.execute(
            text("SELECT integer_value FROM platform_settings WHERE key='max_companies_per_user'")
        ).mappings().first()
    except Exception as exc:
        raise CompanyError("Company limits are unavailable.", 503, "settings_unavailable") from exc
    if not row:
        raise CompanyError("Company limits are unavailable.", 503, "settings_unavailable")
    value = row.get("integer_value")
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise CompanyError("Company limits are unavailable.", 503, "settings_unavailable")
    return value


def _audit_failure(actor_id, code, ip=None):
    """Best-effort safe failure audit after the provisioning transaction rolls back."""
    try:
        with get_session() as db:
            actor = db.get(User, actor_id)
            if actor:
                audit(db, actor, "company.create_failed", target=actor,
                      before={}, after={"code": str(code)[:80]}, ip=ip)
                db.commit()
    except Exception:
        pass


def _public_company(company):
    return {
        "id": company.id, "name": company.name, "company_type": company.company_type,
        "legal_form": company.legal_form, "base_currency": company.base_currency,
        "fiscal_year_start_month": company.fiscal_year_start_month, "tax_id": company.tax_id,
        "status": company.status, "owner_user_id": company.owner_user_id,
        "schema_version": company.schema_version,
        "created_at": company.created_at.isoformat() if company.created_at else None,
    }


public_company_metadata = _public_company


def _link_exclusive(source, destination):
    linked = False
    source_identity = _file_identity(source)
    if source_identity is None:
        raise CompanyError("Company storage is unavailable.", 503, "storage_unavailable")
    try:
        os.link(source, destination)
        linked = True
    except FileExistsError as exc:
        raise CompanyError("Company storage is unavailable.", 503, "storage_conflict") from exc
    destination_identity = None
    try:
        fd = os.open(destination, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            destination_identity = (info.st_dev, info.st_ino, getattr(info, "st_uid", None))
            os.fsync(fd)
        finally:
            os.close(fd)
        if _file_identity(source) != source_identity:
            raise OSError(errno.ESTALE, "temporary file changed")
        os.unlink(source)
        if os.name != "nt":
            dir_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except Exception:
        # Once link(2) succeeds the destination is ours, even if a later fsync
        # fails.  Remove it here; callers must never remove a pre-existing name.
        if linked and destination_identity is not None:
            _unlink_owned(destination, destination_identity)
        raise


def _file_identity(path):
    try:
        info = os.stat(path, follow_symlinks=False)
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode) or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
        return None
    return info.st_dev, info.st_ino, getattr(info, "st_uid", None)


def _unlink_owned(path, identity):
    """Unlink only the regular file whose lstat identity we recorded."""
    try:
        info = os.stat(path, follow_symlinks=False)
        current = (info.st_dev, info.st_ino, getattr(info, "st_uid", None))
        if not stat.S_ISREG(info.st_mode) or current != identity:
            return
        path.unlink()
    except OSError:
        return


def provision_company(actor_id, data, expected_epoch=None, ip=None):
    """Provision one company atomically and return public registry metadata.

    The platform registry row and owner membership remain uncommitted until the
    isolated file has its schema/settings and has been moved into its generated
    final name.  Hook stages are ``temp_created``, ``schema_applied``,
    ``settings_written``, ``file_moved`` and ``before_commit``.
    """
    base = None
    temp_path = None
    final_path = None
    final_identity = None
    temp_identity = None
    actor_for_failure = actor_id
    try:
        normalized = _validate_data(data)
        with get_session() as db:
            db.execute(text("BEGIN IMMEDIATE"))
            actor = _actor_in_transaction(db, actor_id, expected_epoch)
            actor_for_failure = actor.id
            from sqlalchemy import func
            count = db.scalar(select(func.count(Company.id)).where(Company.owner_user_id == actor.id)) or 0
            if count >= _max_companies(db):
                raise CompanyError("You already have the maximum number of companies.", 409, "company_limit")
            filename = _generated_filename()
            company = Company(
                name=normalized["name"], company_type=normalized["company_type"],
                legal_form=normalized["legal_form"], base_currency=normalized["base_currency"],
                fiscal_year_start_month=normalized["fiscal_year_start_month"], tax_id=normalized["tax_id"],
                status="provisioning", owner_user_id=actor.id, db_filename=filename,
                schema_version=SCHEMA_VERSION, created_at=utcnow(),
            )
            db.add(company)
            db.flush()
            db.add(CompanyMembership(user_id=actor.id, company_id=company.id, role="owner", status="active"))
            db.flush()

            base = company_data_dir()
            final_path = _safe_generated_path(base, filename)
            fd, temp_name = tempfile.mkstemp(prefix=".company-", suffix=".db.tmp", dir=str(base))
            os.close(fd)
            temp_path = Path(temp_name)
            if temp_path.is_symlink():
                raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
            temp_identity = _file_identity(temp_path)
            if temp_identity is None:
                raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
            _hook("temp_created")
            apply_migrations(temp_path)
            _hook("schema_applied")
            write_settings(temp_path, normalized)
            _hook("settings_written")
            _link_exclusive(temp_path, final_path)
            final_identity = _file_identity(final_path)
            if final_identity is None:
                raise CompanyError("Company storage path is invalid.", 500, "invalid_storage_path")
            temp_path = None
            temp_identity = None
            _hook("file_moved")
            company.status = "active"
            db.flush()
            audit(db, actor, "company.created", target=actor, before={}, after=_public_company(company), ip=ip)
            _hook("before_commit")
            result = _public_company(company)
            db.commit()
            return result
    except CompanyError as exc:
        _cleanup_files(temp_path, final_path, final_identity, temp_identity)
        _audit_failure(actor_for_failure, exc.code, ip)
        raise
    except (IntegrityError, OperationalError) as exc:
        _cleanup_files(temp_path, final_path, final_identity, temp_identity)
        _audit_failure(actor_for_failure, "platform_conflict", ip)
        if isinstance(exc, OperationalError) and "locked" in str(exc).lower():
            raise CompanyError("Another company change is in progress; retry.", 409, "platform_locked") from exc
        raise _safe_error("platform_conflict", 409) from exc
    except Exception as exc:
        _cleanup_files(temp_path, final_path, final_identity, temp_identity)
        _audit_failure(actor_for_failure, "provision_failed", ip)
        raise _safe_error() from exc


def _cleanup_files(temp_path, final_path, final_owned=False, temp_identity=None):
    # ``final_owned`` is retained as a compatibility parameter; new callers
    # pass the recorded (device, inode, owner) tuple instead of a boolean.
    final_identity = final_owned if isinstance(final_owned, tuple) else None
    if temp_path and temp_identity:
        _unlink_owned(temp_path, temp_identity)
    if final_path and final_identity:
        _unlink_owned(final_path, final_identity)


def _company_id(company_or_id):
    value = getattr(company_or_id, "id", company_or_id)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CompanyError("Company was not found.", 404, "company_not_found") from exc


def _authorized_company(db, company_id, user_id, expected_epoch=None):
    actor = _actor_in_transaction(db, user_id, expected_epoch)
    company = db.get(Company, company_id)
    membership = db.execute(
        select(CompanyMembership).where(
            CompanyMembership.company_id == company_id,
            CompanyMembership.user_id == actor.id,
            CompanyMembership.role == "owner",
            CompanyMembership.status == "active",
        )
    ).scalar_one_or_none()
    if not company or not membership or company.status != "active":
        raise CompanyError("You cannot access this company.", 403, "workspace_denied")
    return actor, company


def _record_denied(user_id, company_id, reason, ip=None):
    try:
        with get_session() as db:
            actor = db.get(User, user_id)
            if actor:
                audit(db, actor, "workspace.denied", target=actor, before={},
                      after={"company_id": company_id, "reason": reason}, ip=ip)
                db.commit()
    except Exception:
        pass


@contextmanager
def open_company_database(company_id, user_id, expected_epoch=None, ip=None):
    """Yield a read-only SQLite connection after a complete platform auth check."""
    db = get_session()
    connection = None
    try:
        db.execute(text("BEGIN"))
        try:
            actor, company = _authorized_company(db, _company_id(company_id), user_id, expected_epoch)
        except CompanyError as exc:
            db.rollback()
            _record_denied(user_id, _company_id(company_id), exc.code, ip)
            raise
        base = company_data_dir()
        path = _safe_generated_path(base, company.db_filename)
        if not path.is_file() or path.is_symlink() or not os.access(path, os.R_OK):
            raise CompanyError("Company database is unavailable.", 503, "company_unavailable")
        try:
            connection = open_read_only(path)
        except (OSError, sqlite3.Error, CompanySchemaError) as exc:
            raise CompanyError("Company database is unavailable.", 503, "company_unavailable") from exc
        # Keep the platform read transaction open while the caller reads.  A
        # concurrent suspension/deactivation cannot change this authorization
        # snapshot halfway through a workspace request.
        yield connection
    finally:
        if connection is not None:
            connection.close()
        try:
            db.rollback()
        finally:
            db.close()


def company_workspace(company_id, user_id, expected_epoch=None, ip=None):
    """Return only this user's company's own settings and schema metadata."""
    try:
        with open_company_database(company_id, user_id, expected_epoch, ip) as connection:
            row = connection.execute(
                """SELECT name, type, legal_form, base_currency,
                          fiscal_year_start_month, tax_id, country, currency_locked
                   FROM company_settings WHERE id=1"""
            ).fetchone()
            version = read_schema_version(connection)
    except CompanyError:
        raise
    except (sqlite3.Error, CompanySchemaError) as exc:
        raise CompanyError("Company database is unavailable.", 503, "company_unavailable") from exc
    if row is None:
        raise CompanyError("Company database is unavailable.", 503, "company_unavailable")
    return {
        "id": _company_id(company_id), "name": row[0], "company_type": row[1],
        "legal_form": row[2], "base_currency": row[3], "fiscal_year_start_month": row[4],
        "tax_id": row[5], "country": row[6], "currency_locked": bool(row[7]),
        "schema_version": version,
    }


def health_check(company):
    """Safely inspect only schema_meta and return flags, never a filesystem path."""
    company_id = _company_id(company)
    try:
        with get_session() as db:
            row = db.get(Company, company_id)
            if not row:
                return {"file_exists": False, "readable": False, "schema_version_matches": False, "healthy": False}
            base = company_data_dir()
            path = _safe_generated_path(base, row.db_filename)
            exists = path.is_file() and not path.is_symlink()
            if not exists:
                return {"file_exists": False, "readable": False, "schema_version_matches": False, "healthy": False}
            connection = None
            try:
                # Health must inspect only schema_meta.  In particular it does
                # not run full schema validation or read company_settings.
                connection = open_read_only(path, validate=False)
                version = read_schema_version(connection)
                readable = True
            except (OSError, sqlite3.Error, CompanySchemaError, TypeError, ValueError):
                readable, version = False, None
            finally:
                if connection is not None:
                    connection.close()
            try:
                actual_version = int(version) if version is not None else None
                registry_version = int(row.schema_version)
            except (TypeError, ValueError):
                actual_version = registry_version = None
            matches = readable and actual_version == registry_version == SCHEMA_VERSION
            return {"file_exists": True, "readable": readable, "schema_version_matches": bool(matches), "healthy": bool(matches)}
    except CompanyError:
        return {"file_exists": False, "readable": False, "schema_version_matches": False, "healthy": False}


def _transition(company_id, actor_id, action, expected_epoch=None, ip=None):
    with get_session() as db:
        db.execute(text("BEGIN IMMEDIATE"))
        actor = _actor_in_transaction(db, actor_id, expected_epoch, standard_only=False)
        if actor.role != "super_admin":
            raise AdminError("Super Admin access required.", 403)
        company = db.get(Company, _company_id(company_id))
        if not company:
            raise CompanyError("Company was not found.", 404, "company_not_found")
        desired = "suspended" if action == "company.suspended" else "active"
        if company.status not in {"active", "suspended"}:
            raise CompanyError("Company is not ready for this action.", 409, "invalid_company_state")
        if company.status == desired:
            raise CompanyError("Company is already in that state.", 409, "invalid_company_state")
        before = {"status": company.status}
        company.status = desired
        db.flush()
        audit(db, actor, action, target=actor, before={"company_id": company.id, **before},
              after={"company_id": company.id, "status": desired}, ip=ip)
        result = _public_company(company)
        db.commit()
        return result


def suspend_company(company_id, actor_id, expected_epoch=None, ip=None):
    return _transition(company_id, actor_id, "company.suspended", expected_epoch, ip)


def reactivate_company(company_id, actor_id, expected_epoch=None, ip=None):
    return _transition(company_id, actor_id, "company.reactivated", expected_epoch, ip)


# Short aliases are useful to route layers while the explicit names remain the
# primary API contract.
suspend = suspend_company
reactivate = reactivate_company

__all__ = [
    "CompanyError", "company_data_dir", "provision_company", "open_company_database",
    "company_workspace", "health_check", "suspend_company", "reactivate_company",
    "suspend", "reactivate", "public_company_metadata",
]
