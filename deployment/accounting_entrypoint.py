"""Deployment gate only; does not patch the frozen app or change accounting data."""
import json
import os
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name('accounting-schema.json')


def super_admin_migration_error(problem, database_file):
    migration = Path(__file__).resolve().parents[1] / 'accounting-software/migrations/super_admin.py'
    return RuntimeError(problem + '\nThis existing file needs the explicit Super Admin upgrade. '
        'Stop all writers and back it up outside Git first, then run in your activated venv:\n'
        f'python "{migration}" --database "{database_file}"\n'
        'Restart the same launcher afterward. Existing passwords/data are retained; no file is reset or migrated automatically.')


def company_migration_error(problem, database_file):
    migration = Path(__file__).resolve().parents[1] / 'accounting-software/migrations/companies.py'
    return RuntimeError(problem + '\nExplicit Step 2 migration required after Step 1. '
        'Stop writers and back up the existing platform file outside Git, then run:\n'
        f'python "{migration}" --database "{database_file}"\n'
        'The platform database is not moved or replaced. No automatic migration is allowed.')


def preflight():
    secret = os.getenv('SECRET_KEY', '')
    if len(secret) < 32 or secret == 'dev-only-change-me':
        raise RuntimeError('Set an explicit strong SECRET_KEY (at least 32 characters).')
    seed_password = os.getenv('ADMIN_PASSWORD', '')
    if len(seed_password) < 12 or seed_password == 'Admin123!':
        raise RuntimeError('Set a strong ADMIN_PASSWORD fallback; existing passwords are not changed.')
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url.startswith('sqlite:///'):
        raise RuntimeError('DATABASE_URL must point to an explicit existing absolute SQLite file.')
    database_file = Path(database_url[len('sqlite:///'):])
    if not database_file.is_absolute():
        raise RuntimeError('DATABASE_URL must use an absolute path, not a relative database file.')
    if not database_file.is_file():
        raise RuntimeError('Existing accounting database is missing. Refusing to create another database.')
    expected_schema = json.loads(SCHEMA_FILE.read_text())
    with sqlite3.connect(database_file.as_uri() + '?mode=ro', uri=True) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing_tables = set(expected_schema) - tables
        if missing_tables:
            problem = 'Existing database lacks required tables: ' + ', '.join(sorted(missing_tables)) + '. No automatic migration is allowed.'
            if missing_tables & {'user_audit_events', 'platform_settings'} and missing_tables.issubset({'user_audit_events', 'platform_settings', 'companies', 'company_memberships'}):
                raise super_admin_migration_error(problem, database_file)
            if missing_tables.issubset({'companies', 'company_memberships'}):
                raise company_migration_error(problem, database_file)
            raise RuntimeError(problem)
        for table, columns in expected_schema.items():
            actual = {row[1]: row[2].upper() for row in connection.execute('PRAGMA table_info(' + table + ')')}
            missing_columns = {column['name'] for column in columns} - set(actual)
            if any(actual.get(column['name']) != column['type'].upper() for column in columns):
                problem = 'Database columns require review: ' + table + '. Refusing automatic migration.'
                if table == 'users' and missing_columns and missing_columns.issubset({'deleted_at', 'last_login_at', 'session_epoch'}) and all(actual.get(column['name']) == column['type'].upper() for column in columns if column['name'] not in missing_columns):
                    raise super_admin_migration_error(problem, database_file)
                if table == 'platform_settings' and missing_columns == {'integer_value'}:
                    raise company_migration_error(problem, database_file)
                raise RuntimeError(problem)
        user_indexes = {row[1]: row[2] for row in connection.execute('PRAGMA index_list(users)')}
        if user_indexes.get('ux_users_email_normalized') != 1:
            raise super_admin_migration_error('Existing users schema lacks the required normalized email unique index.', database_file)
        maximum = connection.execute("SELECT integer_value FROM platform_settings WHERE key='max_companies_per_user'").fetchone()
        if not maximum or not isinstance(maximum[0], int) or not 1 <= maximum[0] <= 100:
            raise company_migration_error('Missing or invalid max_companies_per_user setting.', database_file)
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('SQLite integrity check failed. No application startup performed.')
        if list(connection.execute('PRAGMA foreign_key_check')):
            raise RuntimeError('Existing foreign-key integrity errors require review before deployment.')
        if not connection.execute('SELECT 1 FROM users WHERE email = ?', ('admin@example.com',)).fetchone():
            raise RuntimeError('The original app would seed an administrator. Refusing to alter the existing database.')
        if connection.execute('SELECT COUNT(*) FROM invoices WHERE updated_at IS NULL').fetchone()[0]:
            raise RuntimeError('The original app would backfill invoice timestamps. Review/approve migration separately.')
        if connection.execute("SELECT COUNT(*) FROM invoice_items WHERE item_name = ''").fetchone()[0]:
            raise RuntimeError('The original app would backfill item names. Review/approve migration separately.')


if __name__ == '__main__':
    preflight()
    # Original startup still runs its own init_db/seed code. Preconditions above
    # prevent known migration/seed branches for the received compatible database.
    # Stop any old writer during cutover; no guarantee is made against concurrent changes.
    os.execvp('gunicorn', ['gunicorn', '--bind', '0.0.0.0:8000', '--workers', '1', '--threads', '2', '--access-logfile', '-', 'app:app'])
