import importlib.util
import sqlite3
from pathlib import Path

import pytest
import accounting_entrypoint as entrypoint
from start_preview import configuration

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / 'accounting-software/database.db'


@pytest.fixture()
def configured(monkeypatch, tmp_path):
    path = tmp_path / 'compatible-step1.db'
    with sqlite3.connect(DATABASE.as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(path) as target:
        source.backup(target)
    spec = importlib.util.spec_from_file_location('step1_migration_fixture', ROOT / 'accounting-software/migrations/super_admin.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate_file(path)
    spec = importlib.util.spec_from_file_location('step2_migration_fixture', ROOT / 'accounting-software/migrations/companies.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate_file(path)
    monkeypatch.setenv('SECRET_KEY', 'test-only-long-secret-key-at-least-thirty-two-characters')
    monkeypatch.setenv('ADMIN_PASSWORD', 'test-only-strong-fallback-password')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///' + str(path))


def test_received_database_passes_read_only_preflight(configured):
    entrypoint.preflight()


def test_weak_secret_is_rejected(configured, monkeypatch):
    monkeypatch.setenv('SECRET_KEY', 'weak')
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        entrypoint.preflight()


def test_missing_database_is_not_created(configured, monkeypatch, tmp_path):
    path = tmp_path / 'not-created.db'
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///' + str(path))
    with pytest.raises(RuntimeError, match='missing'):
        entrypoint.preflight()
    assert not path.exists()


class Result:
    def __init__(self, rows): self.rows = rows
    def __iter__(self): return iter(self.rows)
    def fetchone(self): return self.rows[0] if self.rows else None


def override_read_only_connection(monkeypatch, case):
    real_connect = sqlite3.connect
    class Connection:
        def __init__(self, *args, **kwargs): self.real = real_connect(*args, **kwargs)
        def __enter__(self): return self
        def __exit__(self, *args): self.real.close()
        def execute(self, sql, parameters=()):
            if case == 'admin' and sql.startswith('SELECT 1 FROM users'):
                return Result([])
            if case == 'timestamp' and sql.startswith('SELECT COUNT(*) FROM invoices'):
                return Result([(1,)])
            if case == 'item_name' and sql.startswith('SELECT COUNT(*) FROM invoice_items'):
                return Result([(1,)])
            if case == 'column' and sql == 'PRAGMA table_info(invoices)':
                return Result([row for row in self.real.execute(sql) if row[1] != 'updated_at'])
            return self.real.execute(sql, parameters)
    monkeypatch.setattr(entrypoint.sqlite3, 'connect', Connection)


def test_seed_requirement_is_rejected_without_data_changes(configured, monkeypatch):
    override_read_only_connection(monkeypatch, 'admin')
    with pytest.raises(RuntimeError, match='seed an administrator'):
        entrypoint.preflight()


@pytest.mark.parametrize('case', ['timestamp', 'item_name'])
def test_backfill_requirement_is_rejected(configured, monkeypatch, case):
    override_read_only_connection(monkeypatch, case)
    with pytest.raises(RuntimeError, match='backfill'):
        entrypoint.preflight()


def test_missing_schema_column_is_rejected(configured, monkeypatch):
    override_read_only_connection(monkeypatch, 'column')
    with pytest.raises(RuntimeError, match='columns require review'):
        entrypoint.preflight()


def test_http_and_embedded_https_cookie_contexts_are_separate(tmp_path):
    assert 'secure httponly samesite=none' in configuration(3000, tmp_path)
    plain = configuration(3000, tmp_path, plain_http=True)
    assert 'proxy_cookie_flags session httponly samesite=lax' in plain
    assert 'proxy_cookie_flags session secure' not in plain


def test_old_demo_gets_explicit_upgrade_hint_without_writes(monkeypatch, tmp_path):
    import hashlib
    path = tmp_path / 'old-demo.db'
    with sqlite3.connect(DATABASE.as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(path) as target:
        source.backup(target)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///' + str(path))
    monkeypatch.setenv('SECRET_KEY', 'test-only-long-secret-key-at-least-thirty-two-characters')
    monkeypatch.setenv('ADMIN_PASSWORD', 'test-only-strong-fallback-password')
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError) as refused:
        entrypoint.preflight()
    assert 'explicit Super Admin upgrade' in str(refused.value)
    assert 'migrations' in str(refused.value) and 'super_admin.py' in str(refused.value)
    assert str(path) in str(refused.value)
    assert 'reset' in str(refused.value)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    spec = importlib.util.spec_from_file_location('old_demo_upgrade', ROOT / 'accounting-software/migrations/super_admin.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with sqlite3.connect(path) as connection:
        tables = ['users', 'clients', 'invoices', 'invoice_items', 'invoice_audit_trail']
        before_rows = {table: connection.execute('SELECT * FROM ' + table).fetchall() for table in tables}
    module.migrate_file(path)
    with pytest.raises(RuntimeError, match='Explicit Step 2 migration'):
        entrypoint.preflight()
    spec = importlib.util.spec_from_file_location('old_demo_step2_upgrade', ROOT / 'accounting-software/migrations/companies.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate_file(path)
    entrypoint.preflight()
    with sqlite3.connect(path) as connection:
        for table in tables:
            after_rows = connection.execute('SELECT * FROM ' + table).fetchall()
            if table == 'users':
                after_rows = [row[:len(before_rows[table][0])] for row in after_rows] if before_rows[table] else []
            assert after_rows == before_rows[table]


def test_other_missing_tables_are_not_mislabelled_as_super_admin(configured, monkeypatch):
    real_connect = sqlite3.connect
    class Connection:
        def __init__(self, *args, **kwargs): self.real = real_connect(*args, **kwargs)
        def __enter__(self): return self
        def __exit__(self, *args): self.real.close()
        def execute(self, sql, parameters=()):
            if sql.startswith('SELECT name FROM sqlite_master'):
                return Result([row for row in self.real.execute(sql) if row[0] != 'invoices'])
            return self.real.execute(sql, parameters)
    monkeypatch.setattr(entrypoint.sqlite3, 'connect', Connection)
    with pytest.raises(RuntimeError) as refused:
        entrypoint.preflight()
    assert 'invoices' in str(refused.value)
    assert 'explicit Super Admin upgrade' not in str(refused.value)


def test_missing_unique_email_index_requires_explicit_upgrade(configured, monkeypatch):
    real_connect = sqlite3.connect
    class Connection:
        def __init__(self, *args, **kwargs): self.real = real_connect(*args, **kwargs)
        def __enter__(self): return self
        def __exit__(self, *args): self.real.close()
        def execute(self, sql, parameters=()):
            if sql == 'PRAGMA index_list(users)':
                return Result([row for row in self.real.execute(sql) if row[1] != 'ux_users_email_normalized'])
            return self.real.execute(sql, parameters)
    monkeypatch.setattr(entrypoint.sqlite3, 'connect', Connection)
    with pytest.raises(RuntimeError, match='explicit Super Admin upgrade'):
        entrypoint.preflight()
