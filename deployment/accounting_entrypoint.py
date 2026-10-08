"""Deployment gate only; does not patch the frozen app or change accounting data."""
import json
import os
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name('accounting-schema.json')


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
        if not set(expected_schema).issubset(tables):
            raise RuntimeError('Existing database lacks required tables. No automatic migration is allowed.')
        for table, columns in expected_schema.items():
            actual = {row[1]: row[2].upper() for row in connection.execute('PRAGMA table_info(' + table + ')')}
            if any(actual.get(column['name']) != column['type'].upper() for column in columns):
                raise RuntimeError('Database columns require review: ' + table + '. Refusing automatic migration.')
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
