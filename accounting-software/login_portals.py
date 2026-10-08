"""Two login interfaces sharing the existing identity/session/audit mechanism."""
import hmac
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session
from sqlalchemy import func, select, text

from auth_throttle import check_attempt
from database import get_session
from models.user import User
from super_admin.service import record_login

bp = Blueprint('login_portals', __name__)
PORTALS = {
    'user': {'path': '/login', 'template': 'login.html', 'roles': frozenset({'user', 'admin'}), 'destination': '/dashboard'},
    'super_admin': {'path': '/super-admin/login', 'template': 'super_admin/login.html', 'roles': frozenset({'super_admin'}), 'destination': '/super-admin'},
}


def csrf_token():
    token = session.get('csrf_token')
    if not isinstance(token, str) or not token:
        token = session['csrf_token'] = current_app.config['TOKEN_FACTORY']()
    return token


def login_page(portal='user', error=None, status=200, email=''):
    response = current_app.make_response((render_template(PORTALS[portal]['template'], login_csrf=csrf_token(), login_error=error, login_email=email), status))
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response


def authenticate(portal='user'):
    """Portal is fixed by the route, never accepted from a submitted field."""
    options = PORTALS[portal]
    origin = request.headers.get('Origin')
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme not in {'http','https'} or parsed.netloc.lower() != request.host.lower():
            abort(400, description='Cross-origin login rejected.')
    if not request.is_json:
        expected, supplied = session.get('csrf_token'), request.form.get('csrf_token')
        if not isinstance(expected,str) or not expected or not isinstance(supplied,str) or not hmac.compare_digest(expected,supplied):
            abort(400, description='Invalid CSRF token.')
    data = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    if not isinstance(data,dict) or any(not isinstance(data.get(key,''),str) for key in ('email','password')):
        return failure(portal,'Invalid login data.',400)
    email = data.get('email','').strip().lower()
    if len(email)>255 or len(data.get('password',''))>4096:
        return failure(portal,'Invalid email or password.',401)
    # The same operation/buckets protect both login endpoints, preventing a
    # caller from getting another attempt allowance by changing portals.
    limited = check_attempt('login',email)
    if limited is not None:
        if request.is_json: return limited
        response = login_page(portal,'محاولات كثيرة. انتظر ثم أعد المحاولة.',429,email)
        response.headers['Retry-After'] = limited.headers['Retry-After']
        return response
    with get_session() as db:
        # Match the existing session-revocation write locks: a concurrent role or
        # status change cannot race the role/password check and login audit.
        db.execute(text('BEGIN IMMEDIATE'))
        user = db.scalar(select(User).where(func.lower(User.email)==email,User.is_active.is_(True),User.deleted_at.is_(None)))
        if not user or not user.check_password(data.get('password','')) or user.role not in options['roles']:
            return failure(portal,'Invalid email or password.',401,email)
        record_login(db,user,request.remote_addr)
        db.commit()
        session.clear()
        session.update(user_id=user.id,role=user.role,session_epoch=user.session_epoch,csrf_token=current_app.config['TOKEN_FACTORY']())
        if request.is_json:
            response = jsonify({'user':user.to_dict(),'csrf_token':session['csrf_token'],'redirect_url':options['destination']})
        else:
            response = redirect(options['destination'])
        response.headers['Cache-Control']='no-store'
        return response


def failure(portal,message,status,email=''):
    if status == 401:
        session.clear()
    if request.is_json:
        response=jsonify({'error':message});response.status_code=status;response.headers['Cache-Control']='no-store';return response
    arabic = 'البريد الإلكتروني أو كلمة المرور غير صحيحة لهذه الواجهة.' if status==401 else 'بيانات تسجيل الدخول غير صحيحة.'
    return login_page(portal,arabic,status,email)


@bp.route('/super-admin/login',methods=['GET','POST'])
def super_admin_login():
    if request.method=='GET': return login_page('super_admin')
    return authenticate('super_admin')
