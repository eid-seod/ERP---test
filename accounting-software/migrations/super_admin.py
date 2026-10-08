"""Step 1 additive migration; never reads or changes financial tables."""
import argparse
import sqlite3
from pathlib import Path

COLUMNS = {'deleted_at': 'DATETIME', 'last_login_at': 'DATETIME', 'session_epoch': 'INTEGER NOT NULL DEFAULT 0'}
EMAIL_INDEX = 'ux_users_email_normalized'
DDL = [
    'CREATE UNIQUE INDEX IF NOT EXISTS ' + EMAIL_INDEX + ' ON users(lower(email))',
    '''CREATE TABLE IF NOT EXISTS user_audit_events (
    id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    target_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_name VARCHAR(120) NOT NULL, actor_email VARCHAR(255) NOT NULL,
    action VARCHAR(80) NOT NULL, before_data TEXT NOT NULL, after_data TEXT NOT NULL,
    changed_at DATETIME NOT NULL, ip_address VARCHAR(64))''',
    '''CREATE TABLE IF NOT EXISTS platform_settings (
    key VARCHAR(80) PRIMARY KEY, value BOOLEAN NOT NULL, updated_at DATETIME NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS ix_user_audit_events_actor_id ON user_audit_events(actor_id)',
    'CREATE INDEX IF NOT EXISTS ix_user_audit_events_target_id ON user_audit_events(target_id)',
    'CREATE INDEX IF NOT EXISTS ix_user_audit_events_action ON user_audit_events(action)',
    'CREATE INDEX IF NOT EXISTS ix_user_audit_events_changed_at ON user_audit_events(changed_at)',
]


def require_existing_upgrade(engine):
    """Before original init_db: reject existing users schemas pending Step 1.

    Fresh databases retain the existing explicit demo/test initialization behavior.
    Local/production preflight additionally refuses a missing existing database.
    """
    with engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql('PRAGMA table_info(users)')}
        if not columns:
            return
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
        indexes = {row[1]: row[2] for row in connection.exec_driver_sql('PRAGMA index_list(users)')}
        if not set(COLUMNS).issubset(columns) or not {'user_audit_events', 'platform_settings'}.issubset(tables) or indexes.get(EMAIL_INDEX) != 1:
            raise RuntimeError('Existing database requires the explicit Step 1 migration: migrations/super_admin.py --database YOUR_EXISTING_FILE. Startup did not migrate it.')


def apply(connection):
    execute = getattr(connection, 'exec_driver_sql', connection.execute)
    columns = {row[1] for row in execute('PRAGMA table_info(users)')}
    if not {'id', 'email', 'role', 'is_active', 'password_hash'}.issubset(columns):
        raise RuntimeError('A compatible existing users table is required; no database is created.')
    if list(execute('SELECT lower(email) FROM users GROUP BY lower(email) HAVING count(*) > 1')):
        raise RuntimeError('Existing case-insensitive duplicate emails require owner review. No rows or schema were rewritten.')
    for name, definition in COLUMNS.items():
        if name not in columns:
            execute('ALTER TABLE users ADD COLUMN ' + name + ' ' + definition)
    for statement in DDL:
        execute(statement)


def migrate_file(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError('Existing database file is required. Refusing to create one.')
    with sqlite3.connect(path.as_uri() + '?mode=rw', uri=True) as connection:
        connection.execute('BEGIN IMMEDIATE')
        apply(connection)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Back up outside Git and stop writers first. Adds Step 1 users/audit/settings schema only.')
    parser.add_argument('--database', required=True, type=Path)
    args = parser.parse_args()
    migrate_file(args.database)
    print('Step 1 migration applied. Existing users and financial tables were not rewritten.')
