import hashlib
import secrets
import sqlite3

import pytest


def test_existing_file_with_no_users_is_not_initialized(tmp_path):
    from app import create_app
    path = tmp_path / 'partial.db'
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE invoices(id INTEGER PRIMARY KEY, marker TEXT)')
        connection.execute("INSERT INTO invoices VALUES (1,'preserved')")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='Refusing automatic initialization'):
        create_app({'TESTING':True,'DATABASE_URL':'sqlite:///'+path.as_posix(),'SECRET_KEY':secrets.token_hex(32)})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_existing_current_file_does_not_seed_missing_original_admin(tmp_path, monkeypatch):
    from app import create_app
    path = tmp_path / 'current.db'
    config = {'TESTING':True,'DATABASE_URL':'sqlite:///'+path.as_posix(),'SECRET_KEY':secrets.token_hex(32)}
    monkeypatch.setenv('ADMIN_PASSWORD',secrets.token_urlsafe(24))
    create_app(config)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM users WHERE email='admin@example.com'")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='Refusing automatic seeding'):
        create_app(config)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
