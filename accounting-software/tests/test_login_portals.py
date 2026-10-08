import re
import secrets

import pytest
from sqlalchemy import func, select

import database
from app import create_app
from models.user import User
from super_admin.models import PlatformSetting, UserAuditEvent


@pytest.fixture()
def setup(tmp_path):
    app = create_app({'TESTING':True,'SECRET_KEY':secrets.token_hex(32),'DATABASE_URL':'sqlite:///'+str(tmp_path/'portals.db')})
    accounts = {}
    with database.get_session() as db:
        for role in ('user','admin','super_admin'):
            password = secrets.token_urlsafe(18)
            user = User(name=role,email=role+'@fixture.invalid',role=role)
            user.set_password(password);db.add(user);db.flush()
            accounts[role] = {'email':user.email,'password':password,'id':user.id}
        db.commit()
    return app,accounts


def token(client,path):
    page = client.get(path)
    assert page.status_code==200
    return re.search(r'name="csrf_token" value="([^"]+)"',page.text).group(1)


@pytest.mark.parametrize('path,heading', [('/login','تسجيل دخول المستخدمين'),('/super-admin/login','تسجيل دخول Super Admin')])
def test_native_interfaces_are_distinct_private_and_empty(setup,path,heading):
    page = setup[0].test_client().get(path)
    assert page.status_code==200 and heading in page.text
    assert 'dir="rtl"' in page.text and '/static/css/app.css' in page.text
    assert '/static/js/app.js' not in page.text
    assert 'admin@example.com' not in page.text and 'Admin123!' not in page.text
    assert 'name="csrf_token"' in page.text and 'action="'+path+'"' in page.text
    assert page.headers['Cache-Control']=='no-store'
    assert page.headers['X-Robots-Tag']=='noindex, nofollow'


@pytest.mark.parametrize('role,path,destination', [('user','/login','/dashboard'),('admin','/login','/dashboard'),('super_admin','/super-admin/login','/super-admin')])
def test_right_portal_json_fixed_redirect_session_and_audit(setup,role,path,destination):
    app,accounts=setup;client=app.test_client()
    initial=token(client,path)
    response=client.post(path,json={**accounts[role],'role':'super_admin','next':'https://foreign.invalid','redirect_url':'https://foreign.invalid'})
    assert response.status_code==200 and response.json['redirect_url']==destination
    assert response.json['user']['role']==role and response.json['csrf_token']!=initial
    with client.session_transaction() as state:
        assert state['user_id']==accounts[role]['id'] and state['role']==role
        assert accounts[role]['password'] not in str(dict(state))
    with database.get_session() as db:
        row=db.scalar(select(UserAuditEvent).where(UserAuditEvent.action=='auth.login'))
        assert row.actor_id==accounts[role]['id']
        assert accounts[role]['password'] not in row.after_data+row.before_data
    assert client.get(destination).status_code==200


@pytest.mark.parametrize('role,path', [('super_admin','/login'),('user','/super-admin/login'),('admin','/super-admin/login')])
def test_wrong_portal_creates_no_session_or_audit(setup,role,path):
    app,accounts=setup;client=app.test_client()
    response=client.post(path,json={**accounts[role],'role':'super_admin'})
    assert response.status_code==401
    assert response.json['error']=='Invalid email or password.'
    with client.session_transaction() as state:assert 'user_id' not in state
    with database.get_session() as db:
        assert db.scalar(select(func.count(UserAuditEvent.id)).where(UserAuditEvent.action=='auth.login'))==0


@pytest.mark.parametrize('role,path,destination', [('user','/login','/dashboard'),('super_admin','/super-admin/login','/super-admin')])
def test_native_post_requires_csrf_then_redirects(setup,role,path,destination):
    app,accounts=setup;client=app.test_client()
    body={'email':accounts[role]['email'],'password':accounts[role]['password']}
    assert client.post(path,data=body).status_code==400
    csrf=token(client,path)
    assert client.post(path,data={**body,'csrf_token':'wrong'}).status_code==400
    response=client.post(path,data={**body,'csrf_token':csrf,'next':'//foreign.invalid'})
    assert response.status_code==302 and response.location==destination


@pytest.mark.parametrize('path', ['/login','/super-admin/login'])
def test_wrong_password_native_safe_error_never_echoes_password(setup,path):
    app,accounts=setup;client=app.test_client();csrf=token(client,path)
    role='super_admin' if path.startswith('/super-admin') else 'user'
    wrong=secrets.token_urlsafe(24)
    response=client.post(path,data={'email':accounts[role]['email'],'password':wrong,'csrf_token':csrf})
    assert response.status_code==401 and 'role="alert"' in response.text
    assert wrong not in response.text and 'name="csrf_token"' in response.text


@pytest.mark.parametrize('path', ['/login','/super-admin/login'])
def test_cross_origin_login_and_malformed_json_are_rejected(setup,path):
    client=setup[0].test_client()
    assert client.post(path,json={},headers={'Origin':'https://foreign.invalid'}).status_code==400
    assert client.post(path,json=[1,2]).status_code==400
    assert client.post(path,json={'email':[],'password':{}}).status_code==400
    assert client.post(path,json={'email':'missing@fixture.invalid','password':'wrong'},headers={'Origin':'https://localhost'}).status_code==401


def test_shared_login_limiter_cannot_be_bypassed_by_switching_portal(setup):
    app,accounts=setup;app.config['AUTH_ATTEMPT_LIMITS']={'login':{'ip':2,'email':2,'window':3600}}
    client=app.test_client();csrf=token(client,'/super-admin/login')
    body={'email':'missing@fixture.invalid','password':'wrong'}
    assert client.post('/login',json=body).status_code==401
    assert client.post('/super-admin/login',json=body).status_code==401
    csrf=token(client,'/super-admin/login')
    response=client.post('/super-admin/login',data={**body,'csrf_token':csrf})
    assert response.status_code==429 and response.headers['Retry-After']
    assert 'محاولات كثيرة' in response.text


def test_registration_still_flag_gated_and_standard_only(setup):
    app,accounts=setup;client=app.test_client()
    assert client.get('/register').status_code==404
    assert 'href="/register"' not in client.get('/login').text
    with database.get_session() as db:
        setting=db.get(PlatformSetting,'public_registration_enabled')
        if setting is None:
            db.add(PlatformSetting(key='public_registration_enabled',value=True))
        else:
            setting.value=True
        db.commit()
    assert 'href="/register"' in client.get('/login').text
    assert 'href="/register"' not in client.get('/super-admin/login').text
    response=client.get('/register')
    assert 'href="/login"' in response.text
    csrf=re.search(r'name="csrf_token" value="([^"]+)"',response.text).group(1)
    password=secrets.token_urlsafe(18)
    response=client.post('/register',data={'name':'Signup','email':'signup@fixture.invalid','password':password,'csrf_token':csrf,'role':'super_admin'})
    assert response.status_code==302 and response.location=='/login?registered=1'
    assert client.post('/super-admin/login',json={'email':'signup@fixture.invalid','password':password}).status_code==401
    response=client.post('/login',json={'email':'signup@fixture.invalid','password':password})
    assert response.status_code==200 and response.json['user']['role']=='user'


@pytest.mark.parametrize('role,path', [('user','/login'),('super_admin','/super-admin/login')])
@pytest.mark.parametrize('change', ['inactive','deleted'])
def test_inactive_or_deleted_rejected_and_revoked_session_can_open_portal(setup,role,path,change):
    app,accounts=setup;client=app.test_client()
    assert client.post(path,json=accounts[role]).status_code==200
    with database.get_session() as db:
        user=db.get(User,accounts[role]['id'])
        if change=='inactive':user.is_active=False
        else:
            from super_admin.models import utcnow
            user.deleted_at=utcnow()
        db.commit()
    destination='/super-admin' if role=='super_admin' else '/dashboard'
    response=client.get(destination)
    assert response.status_code==302 and response.location==path
    assert client.get(path).status_code==200
    assert client.post(path,json=accounts[role]).status_code==401


@pytest.mark.parametrize('failure_mode', ['wrong_password','wrong_portal'])
def test_rejected_switch_clears_prior_identity(setup,failure_mode):
    app,accounts=setup;client=app.test_client()
    assert client.post('/super-admin/login',json=accounts['super_admin']).status_code==200
    csrf=token(client,'/login')
    body={'email':accounts['user']['email'],'password':'wrong' if failure_mode=='wrong_password' else accounts['super_admin']['password'],'csrf_token':csrf}
    if failure_mode=='wrong_portal':body['email']=accounts['super_admin']['email']
    response=client.post('/login',data=body)
    assert response.status_code==401 and 'name="csrf_token"' in response.text
    with client.session_transaction() as state:
        assert 'user_id' not in state and state['csrf_token']!=csrf
    assert client.get('/me').status_code==401


@pytest.mark.parametrize('role,path,destination', [('user','/login','/login'),('admin','/login','/login'),('super_admin','/super-admin/login','/super-admin/login')])
def test_logout_from_accounting_dashboard_returns_role_portal(setup,role,path,destination):
    app,accounts=setup;client=app.test_client()
    result=client.post(path,json=accounts[role]);assert result.status_code==200
    assert client.get('/dashboard').status_code==200
    response=client.post('/logout',json={'next':'https://foreign.invalid'},headers={'X-CSRF-Token':result.json['csrf_token']})
    assert response.status_code==200 and response.json['redirect_url']==destination
    with client.session_transaction() as state:assert 'user_id' not in state
