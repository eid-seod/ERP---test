import json
import re
import secrets
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import event, func, select

import database
from app import create_app
from models.user import User
from super_admin.models import PlatformSetting, UserAuditEvent, utcnow
from migrations.super_admin import migrate_file


@pytest.fixture()
def setup(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'users-test.db')})
    identities = {}
    with database.get_session() as db:
        for key, role in [('owner', 'super_admin'), ('second', 'super_admin'), ('member', 'user')]:
            password = secrets.token_urlsafe(18)
            user = User(name=key.title(), email=key + '@fixture.invalid', role=role)
            user.set_password(password)
            db.add(user)
            db.flush()
            identities[key] = {'id': user.id, 'email': user.email, 'password': password}
        db.commit()
    return app, identities


def signin(app, identity):
    client = app.test_client()
    response = client.post('/login', json={'email': identity['email'], 'password': identity['password']})
    assert response.status_code == 200
    return client, {'X-CSRF-Token': response.json['csrf_token']}


def operator(setup):
    app, identities = setup
    client, headers = signin(app, identities['owner'])
    return app, identities, client, headers


def post(client, headers, path, data=None):
    return client.post('/super-admin' + path, json=data or {}, headers=headers)


@pytest.mark.parametrize('path', ['', '/users', '/users/new', '/audit', '/settings'])
def test_unauthenticated_redirects_to_existing_login(setup, path):
    response = setup[0].test_client().get('/super-admin' + path)
    assert response.status_code == 302
    assert response.headers['Location'] == '/login'


@pytest.mark.parametrize('role', ['user', 'admin'])
def test_existing_roles_are_forbidden_and_no_nav_link(setup, role):
    app, identities = setup
    if role == 'admin':
        with database.get_session() as db:
            user = db.get(User, identities['member']['id'])
            user.role = 'admin'
            db.commit()
    client, headers = signin(app, identities['member'])
    for path in ['', '/users', '/users/new', '/audit', '/settings']:
        assert client.get('/super-admin' + path).status_code == 403
    assert post(client, headers, '/users/new', {'name': 'Denied', 'email': 'denied@fixture.invalid'}).status_code == 403
    assert 'href="/super-admin"' not in client.get('/dashboard').text


def test_native_pages_reuse_shell_and_never_include_financial_js(setup):
    app, identities, client, headers = operator(setup)
    paths = ['', '/users', '/users/new', '/audit', '/settings', '/users/' + str(identities['member']['id']), '/users/' + str(identities['member']['id']) + '/edit']
    for path in paths:
        response = client.get('/super-admin' + path)
        assert response.status_code == 200
        assert 'dir="rtl"' in response.text
        assert '/static/css/app.css' in response.text
        assert '/static/js/super_admin.js' in response.text
        assert '/static/js/app.js' not in response.text
        assert 'loadDashboard' not in response.text
        assert 'id="invoice-rows"' not in response.text
    assert 'href="/super-admin"' in client.get('/dashboard').text


@pytest.mark.parametrize('method,path,data', [
    ('post', '/users/new', {'name': 'Blocked', 'email': 'blocked@fixture.invalid'}),
    ('post', '/settings', {'enabled': True}),
    ('put', '/users/2/status', {'action': 'deactivate'}),
    ('delete', '/users/2/delete', {}),
])
def test_every_new_write_requires_csrf(setup, method, path, data):
    app, identities, client, headers = operator(setup)
    for invalid in [{}, {'X-CSRF-Token': 'invalid-test-token'}]:
        response = getattr(client, method)('/super-admin' + path, json=data, headers=invalid)
        assert response.status_code == 400


def test_post_form_csrf_and_get_cannot_mutate(setup):
    app, identities, client, headers = operator(setup)
    target = identities['member']['id']
    response = client.post('/super-admin/users/' + str(target) + '/status', data={'action': 'deactivate', 'csrf_token': headers['X-CSRF-Token']})
    assert response.status_code == 302
    for path in ['/users/' + str(target) + '/delete', '/users/' + str(target) + '/restore', '/users/' + str(target) + '/password']:
        assert client.get('/super-admin' + path).status_code == 405
    assert client.patch('/super-admin/settings', json={'enabled': True}, headers=headers).status_code == 405


def test_create_generate_once_unique_email_and_policy(setup):
    app, identities, client, headers = operator(setup)
    response = post(client, headers, '/users/new', {'name': 'New Person', 'email': 'NEW@fixture.invalid', 'role': 'admin'})
    assert response.status_code == 201
    temporary = response.json['temporary_password']
    assert len(temporary) >= 8
    user = response.json['user']
    assert user['email'] == 'new@fixture.invalid'
    assert 'temporary_password' not in client.get('/super-admin/users/' + str(user['id']), headers={'Accept': 'application/json'}).json
    assert temporary not in client.get('/super-admin/audit').text
    assert temporary not in str(dict(client.get_cookie('session').__dict__))
    assert post(client, headers, '/users/new', {'name': 'Duplicate', 'email': 'NEW@fixture.invalid'}).status_code == 409
    assert post(client, headers, '/users/new', {'name': 'Short', 'email': 'short@fixture.invalid', 'password': secrets.token_hex(3)}).status_code == 400
    assert post(client, headers, '/users/new', {'name': 5, 'email': 'bad@fixture.invalid'}).status_code == 400
    assert signin(app, {'email': user['email'], 'password': temporary})[0]


def test_self_protection_for_all_three_actions(setup):
    app, identities, client, headers = operator(setup)
    uid = identities['owner']['id']
    assert post(client, headers, '/users/' + str(uid) + '/status', {'action': 'deactivate'}).status_code == 409
    assert post(client, headers, '/users/' + str(uid) + '/delete').status_code == 409
    response = post(client, headers, '/users/' + str(uid) + '/edit', {'name': 'Owner', 'email': identities['owner']['email'], 'role': 'admin'})
    assert response.status_code == 409
    with database.get_session() as db:
        user = db.get(User, uid)
        assert user.is_active and user.role == 'super_admin' and user.deleted_at is None


@pytest.mark.parametrize('action', ['deactivate', 'delete', 'demote'])
def test_last_remaining_active_super_admin_is_protected(setup, action):
    app, identities, client, headers = operator(setup)
    assert post(client, headers, '/users/' + str(identities['second']['id']) + '/status', {'action': 'deactivate'}).status_code == 200
    uid = identities['owner']['id']
    if action == 'deactivate':
        response = post(client, headers, '/users/' + str(uid) + '/status', {'action': 'deactivate'})
    elif action == 'delete':
        response = post(client, headers, '/users/' + str(uid) + '/delete')
    else:
        response = post(client, headers, '/users/' + str(uid) + '/edit', {'name': 'Owner', 'email': identities['owner']['email'], 'role': 'user'})
    assert response.status_code == 409
    assert 'last active' in response.json['error']


def test_legacy_admin_cannot_create_edit_or_delete_super_admin(setup):
    app, identities = setup
    with database.get_session() as db:
        db.get(User, identities['member']['id']).role = 'admin'
        db.commit()
    client, headers = signin(app, identities['member'])
    target = identities['owner']['id']
    assert client.post('/users', json={'name': 'Elevate', 'email': 'elevate@fixture.invalid', 'password': secrets.token_urlsafe(12), 'role': 'super_admin'}, headers=headers).status_code == 403
    assert client.patch('/users/' + str(target), json={'name': 'Changed'}, headers=headers).status_code == 403
    assert client.delete('/users/' + str(target), headers=headers).status_code == 403
    assert client.patch('/users/' + str(identities['member']['id']), json={'role': 'super_admin'}, headers=headers).status_code == 403


def test_session_revocation_deactivate_soft_delete_restore_reset(setup):
    app, identities, client, headers = operator(setup)
    member, member_headers = signin(app, identities['member'])
    uid = identities['member']['id']
    assert post(client, headers, '/users/' + str(uid) + '/status', {'action': 'deactivate'}).status_code == 200
    assert member.get('/me').status_code == 401
    assert member.post('/login', json=identities['member']).status_code == 401
    assert post(client, headers, '/users/' + str(uid) + '/status', {'action': 'activate'}).status_code == 200
    member, member_headers = signin(app, identities['member'])
    assert post(client, headers, '/users/' + str(uid) + '/delete').status_code == 200
    assert member.get('/dashboard').status_code == 302
    normal_list = client.get('/super-admin/users', headers={'Accept': 'application/json'}).json['users']
    assert uid not in [row['id'] for row in normal_list]
    deleted = client.get('/super-admin/users?status=deleted', headers={'Accept': 'application/json'}).json['users']
    assert uid in [row['id'] for row in deleted]
    with database.get_session() as db:
        assert db.get(User, uid) is not None
    assert post(client, headers, '/users/' + str(uid) + '/restore').status_code == 200
    assert member.post('/login', json=identities['member']).status_code == 401
    assert post(client, headers, '/users/' + str(uid) + '/status', {'action': 'activate'}).status_code == 200
    member, member_headers = signin(app, identities['member'])
    response = post(client, headers, '/users/' + str(uid) + '/password')
    assert response.status_code == 200
    assert member.get('/me').status_code == 401
    assert member.post('/login', json=identities['member']).status_code == 401
    assert member.post('/login', json={'email': identities['member']['email'], 'password': response.json['temporary_password']}).status_code == 200


def test_edit_demotes_other_super_admin_and_revokes_cookie(setup):
    app, identities, client, headers = operator(setup)
    other, unused = signin(app, identities['second'])
    uid = identities['second']['id']
    response = post(client, headers, '/users/' + str(uid) + '/edit', {'name': 'Other', 'email': identities['second']['email'], 'role': 'user'})
    assert response.status_code == 200
    assert other.get('/super-admin').status_code == 302


def test_settings_off_by_default_and_toggle_audited(setup):
    app, identities, client, headers = operator(setup)
    body = {'name': 'Public Fixture', 'email': 'public@fixture.invalid', 'password': secrets.token_urlsafe(12)}
    assert client.post('/register', json=body).status_code == 404
    assert client.get('/register').status_code == 404
    assert client.get('/super-admin/settings', headers={'Accept': 'application/json'}).json['public_registration_enabled'] is False
    assert post(client, headers, '/settings', {'enabled': True}).status_code == 200
    assert app.test_client().post('/register', json=body).status_code == 201
    assert post(client, headers, '/settings', {'enabled': False}).status_code == 200
    assert post(client, headers, '/settings', {'enabled': []}).status_code == 400
    events = client.get('/super-admin/audit?action=registration.toggle', headers={'Accept': 'application/json'}).json['events']
    assert len(events) == 2
    assert events[0]['after']['public_registration_enabled'] is False


def test_filters_sort_pagination_details_and_audit(setup):
    app, identities, client, headers = operator(setup)
    with database.get_session() as db:
        example = db.get(User, identities['member']['id'])
        for i in range(25):
            db.add(User(name='Search Fixture ' + str(i).zfill(2), email='search' + str(i) + '@fixture.invalid', role='user', password_hash=example.password_hash))
        db.commit()
    response = client.get('/super-admin/users?q=Search&role=user&status=active&sort=name&direction=desc&per_page=10&page=2', headers={'Accept': 'application/json'})
    assert response.status_code == 200
    assert response.json['pagination']['total'] == 25
    assert len(response.json['users']) == 10
    uid = identities['member']['id']
    for i in range(21):
        assert post(client, headers, '/users/' + str(uid) + '/edit', {'name': 'Member ' + str(i), 'email': identities['member']['email'], 'role': 'user'}).status_code == 200
    html = client.get('/super-admin/users/' + str(uid)).text
    assert '/super-admin/users/' + str(uid) + '?page=2' in html
    today = utcnow().date().isoformat()
    response = client.get('/super-admin/audit?actor=' + str(identities['owner']['id']) + '&action=user.edit&from=' + today + '&to=' + today + '&per_page=10&page=2', headers={'Accept': 'application/json'})
    assert response.status_code == 200
    assert response.json['pagination']['total'] == 21
    assert len(response.json['events']) == 10
    assert client.get('/super-admin/users?sort=unsafe').status_code == 400
    assert client.get('/super-admin/users?page=0').status_code == 400
    assert client.get('/super-admin/audit?from=invalid').status_code == 400


def test_every_admin_mutation_audited_without_passwords(setup):
    app, identities, client, headers = operator(setup)
    secret = secrets.token_urlsafe(18)
    created = post(client, headers, '/users/new', {'name': 'Audited', 'email': 'audited@fixture.invalid', 'password': secret}).json['user']
    uid = created['id']
    calls = [('/edit', {'name': 'Updated', 'email': 'audited@fixture.invalid', 'role': 'admin'}), ('/status', {'action': 'deactivate'}), ('/status', {'action': 'activate'}), ('/password', {'password': secrets.token_urlsafe(18)}), ('/delete', {}), ('/restore', {})]
    for path, data in calls:
        assert post(client, headers, '/users/' + str(uid) + path, data).status_code == 200
    response = client.get('/super-admin/users/' + str(uid), headers={'Accept': 'application/json'})
    actions = {row['action'] for row in response.json['events']}
    assert {'user.create', 'user.edit', 'user.deactivate', 'user.activate', 'user.password_reset', 'user.soft_delete', 'user.restore'}.issubset(actions)
    dump = json.dumps(response.json)
    assert secret not in dump
    assert 'password_hash' not in dump
    assert all(row['actor_id'] == identities['owner']['id'] and row['timestamp'] and row['ip_address'] for row in response.json['events'])


def test_dashboard_counts_last_ten_login_history_and_info(setup):
    app, identities, client, headers = operator(setup)
    with database.get_session() as db:
        actor = db.get(User, identities['owner']['id'])
        for i in range(12):
            db.add(UserAuditEvent(actor_id=actor.id, target_id=actor.id, actor_name=actor.name, actor_email=actor.email, action='auth.login', before_data='{}', after_data='{}', changed_at=utcnow() - timedelta(days=8)))
        db.commit()
    result = client.get('/super-admin', headers={'Accept': 'application/json'}).json
    assert result['counts']['total'] == 4
    assert result['counts']['active'] == 4
    assert result['counts']['inactive'] == 0
    assert result['counts']['locked'] == 0 and result['counts']['lockout_supported'] is False
    assert result['counts']['by_role']['super_admin'] == 2
    assert result['counts']['logins_7_days'] == 1
    assert len(result['events']) == 10
    assert result['system']['version'] and result['system']['environment']


def test_super_admin_area_does_not_query_financial_tables(setup):
    app, identities, client, headers = operator(setup)
    statements = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())
    event.listen(database._engine, 'before_cursor_execute', capture)
    try:
        for path in ['', '/users', '/users/new', '/audit', '/settings', '/users/' + str(identities['member']['id'])]:
            assert client.get('/super-admin' + path).status_code == 200
        new = post(client, headers, '/users/new', {'name': 'Privacy Fixture', 'email': 'privacy@fixture.invalid'}).json['user']
        assert post(client, headers, '/users/' + str(new['id']) + '/status', {'action': 'deactivate'}).status_code == 200
        assert post(client, headers, '/settings', {'enabled': True}).status_code == 200
    finally:
        event.remove(database._engine, 'before_cursor_execute', capture)
    assert statements
    assert not any(re.search(r'\b(invoices|clients|invoice_items|invoice_audit_trail|audit_trail)\b', statement) for statement in statements)


def test_concurrent_cross_deactivations_leave_an_active_super_admin(setup):
    app, identities = setup
    left, left_headers = signin(app, identities['owner'])
    right, right_headers = signin(app, identities['second'])
    def change(client, headers, target):
        return post(client, headers, '/users/' + str(target) + '/status', {'action': 'deactivate'}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(change, left, left_headers, identities['second']['id'])
        second = executor.submit(change, right, right_headers, identities['owner']['id'])
        statuses = [first.result(), second.result()]
    assert statuses.count(200) == 1
    assert all(code in {200, 302, 403, 409} for code in statuses)
    with database.get_session() as db:
        assert db.scalar(select(func.count(User.id)).where(User.role == 'super_admin', User.is_active.is_(True), User.deleted_at.is_(None))) == 1


def test_first_cli_is_interactive_secret_and_first_only(tmp_path, monkeypatch):
    app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'cli.db')})
    for name in ['SUPER_ADMIN_EMAIL', 'SUPER_ADMIN_NAME', 'SUPER_ADMIN_PASSWORD']:
        monkeypatch.delenv(name, raising=False)
    password = secrets.token_urlsafe(18)
    result = app.test_cli_runner().invoke(args=['create-super-admin'], input='bootstrap@fixture.invalid\n' + password + '\n' + password + '\n')
    assert result.exit_code == 0
    assert password not in result.output
    with database.get_session() as db:
        user = db.scalar(select(User).where(User.email == 'bootstrap@fixture.invalid'))
        assert user.role == 'super_admin' and user.check_password(password)
        assert db.scalar(select(func.count(UserAuditEvent.id)).where(UserAuditEvent.action == 'super_admin.bootstrap')) == 1
    result = app.test_cli_runner().invoke(args=['create-super-admin'], input='again@fixture.invalid\n' + password + '\n' + password + '\n')
    assert result.exit_code != 0
    assert 'already exists' in result.output


def test_additive_migration_is_idempotent_and_keeps_existing_rows(tmp_path):
    path = tmp_path / 'legacy-fixture.db'
    original = ('Fixture', 'legacy@fixture.invalid', secrets.token_hex(24), 'admin', 1, '2026-01-01')
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)')
        connection.execute('INSERT INTO users VALUES (1,?,?,?,?,?,?)', original)
        connection.execute('CREATE TABLE invoices(id INTEGER PRIMARY KEY, marker TEXT)')
        connection.execute('INSERT INTO invoices VALUES (1, "fixture-only-sentinel")')
    for repeat in range(2):
        migrate_file(path)
        with sqlite3.connect(path) as connection:
            assert connection.execute('SELECT name,email,password_hash,role,is_active,created_at FROM users').fetchone() == original
            assert connection.execute('SELECT marker FROM invoices').fetchone()[0] == 'fixture-only-sentinel'
            assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert connection.execute('SELECT session_epoch,deleted_at,last_login_at FROM users').fetchone() == (0, None, None)
            assert connection.execute('SELECT count(*) FROM user_audit_events').fetchone()[0] == 0
    missing = tmp_path / 'missing.db'
    with pytest.raises(RuntimeError):
        migrate_file(missing)
    assert not missing.exists()


def test_existing_unmigrated_startup_is_rejected_without_writes(tmp_path):
    import hashlib
    path = tmp_path / 'unmigrated-existing.db'
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)')
        connection.execute('INSERT INTO users VALUES (1,?,?,?,?,?,?)', ('Fixture', 'legacy@fixture.invalid', secrets.token_hex(24), 'admin', 1, '2026-01-01'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='explicit Step 1 migration'):
        create_app({'TESTING': True, 'DATABASE_URL': 'sqlite:///' + str(path)})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with sqlite3.connect(path) as connection:
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {'users'}


def test_mixed_case_emails_cannot_be_duplicated(setup):
    app, identities, client, headers = operator(setup)
    with database.get_session() as db:
        example = db.get(User, identities['member']['id'])
        db.add(User(name='Mixed Case', email='MIXED@fixture.invalid', role='user', password_hash=example.password_hash))
        db.commit()
    assert post(client, headers, '/users/new', {'name': 'Duplicate', 'email': 'mixed@fixture.invalid'}).status_code == 409
    assert post(client, headers, '/users/' + str(identities['member']['id']) + '/edit', {'name': 'Duplicate', 'email': 'mixed@fixture.invalid', 'role': 'user'}).status_code == 409
    assert post(client, headers, '/settings', {'enabled': True}).status_code == 200
    public = app.test_client()
    assert public.post('/register', json={'name': 'Duplicate', 'email': 'mixed@fixture.invalid', 'password': secrets.token_urlsafe(18)}).status_code == 400
    assert public.post('/login', json={'email': 'mixed@fixture.invalid', 'password': identities['member']['password']}).status_code == 200


def test_duplicate_existing_emails_require_manual_review_without_changes(tmp_path):
    import hashlib
    path = tmp_path / 'duplicate-existing.db'
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at TEXT)')
        for uid, email in [(1, 'MIXED@fixture.invalid'), (2, 'mixed@fixture.invalid')]:
            connection.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', (uid, 'Fixture', email, secrets.token_hex(24), 'user', 1, '2026-01-01'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='duplicate emails'):
        migrate_file(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
