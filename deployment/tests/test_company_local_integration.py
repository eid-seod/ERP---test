"""Exercise the actual isolated-module launcher, not accounting cwd imports."""
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_launcher_login_signup_and_company_in_isolated_interpreter(tmp_path):
    environment = os.environ.copy()
    environment.update(DATABASE_URL='sqlite:///' + (tmp_path / 'platform.db').as_posix(), SECRET_KEY=secrets.token_hex(32), ADMIN_PASSWORD=secrets.token_urlsafe(24), COMPANY_DATA_DIR=str(tmp_path / 'companydata'))
    code = '''
import sys,secrets
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'deployment'))
from run_local import load_application,SameOriginApplications
from werkzeug.test import Client
from werkzeug.wrappers import Response
accounting=load_application('_launcher_accounting',root/'accounting-software')
portfolio=load_application('_launcher_portfolio',root/'portfolio')
from database import get_session
from super_admin.models import PlatformSetting
with get_session() as db:
    db.add(PlatformSetting(key='public_registration_enabled',value=True));db.commit()
client=Client(SameOriginApplications(portfolio,accounting),Response)
assert client.get('/').status_code==200
password=secrets.token_urlsafe(18)
assert client.post('/register',json={'name':'Fixture','email':'launcher@fixture.invalid','password':password}).status_code==201
response=client.post('/login',json={'email':'launcher@fixture.invalid','password':password})
assert response.status_code==200,response.text
csrf=response.json['csrf_token']
response=client.post('/companies/new',json={'name':'Fixture','company_type':'industrial','legal_form':'sole_proprietorship','base_currency':'EGP','fiscal_year_start_month':1},headers={'X-CSRF-Token':csrf})
assert response.status_code==201,response.text
assert client.get('/companies/'+str(response.json['company']['id'])).status_code==200
'''
    result = subprocess.run([sys.executable, '-c', code, str(ROOT)], env=environment, cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
