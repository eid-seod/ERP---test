import hmac
import math
from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_, select

from database import get_session
from models.user import User
from .models import UserAuditEvent, utcnow
from .service import ACTIONS, ROLES, AdminError, mutate, registration_enabled, snapshot

bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')


def wants_json():
    return request.is_json or request.accept_mimetypes.best == 'application/json'


@bp.before_request
def protect_area():
    user = g.get('super_identity')
    if not user:
        return redirect('/super-admin/login')
    if user.role != 'super_admin':
        abort(403)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        expected = session.get('csrf_token')
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not isinstance(expected, str) or not isinstance(supplied, str) or not expected or not hmac.compare_digest(expected, supplied):
            abort(400, description='Invalid CSRF token.')


@bp.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@bp.errorhandler(AdminError)
def admin_error(error):
    if wants_json():
        return jsonify({'error': str(error)}), error.status
    return render_template('super_admin/error.html', message=str(error)), error.status


def payload():
    data = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    if not isinstance(data, dict):
        raise AdminError('Invalid request data.')
    for field in ('name', 'email', 'role', 'password'):
        if field in data and not isinstance(data[field], str):
            raise AdminError('Invalid field: ' + field)
    return data


def paging():
    try:
        page = int(request.args.get('page', '1'))
        size = int(request.args.get('per_page', '20'))
        if page < 1 or size < 1 or size > 100:
            raise ValueError
    except ValueError as error:
        raise AdminError('Invalid pagination.') from error
    return page, size


def paginated(db, query):
    page, size = paging()
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    items = list(db.scalars(query.offset((page - 1) * size).limit(size)))
    return items, {'page': page, 'per_page': size, 'total': total, 'pages': max(1, math.ceil(total / size))}


def page_url(page):
    args = {**(request.view_args or {}), **request.args.to_dict()}
    args['page'] = page
    return url_for(request.endpoint, **args)


@bp.context_processor
def navigation():
    return {'roles': ROLES, 'page_url': page_url, 'csrf_token': session.get('csrf_token', '')}


@bp.get('')
@bp.get('/')
def dashboard():
    with get_session() as db:
        alive = User.deleted_at.is_(None)
        counts = {'total': db.scalar(select(func.count(User.id)).where(alive)),
            'active': db.scalar(select(func.count(User.id)).where(alive, User.is_active.is_(True))),
            'inactive': db.scalar(select(func.count(User.id)).where(alive, User.is_active.is_(False))),
            'locked': 0, 'lockout_supported': False,
            'logins_7_days': db.scalar(select(func.count(UserAuditEvent.id)).where(UserAuditEvent.action == 'auth.login', UserAuditEvent.changed_at >= utcnow() - timedelta(days=7)))}
        counts['by_role'] = {role: count for role, count in db.execute(select(User.role, func.count(User.id)).where(alive).group_by(User.role))}
        latest = [entry.to_dict() for entry in db.scalars(select(UserAuditEvent).order_by(UserAuditEvent.changed_at.desc(), UserAuditEvent.id.desc()).limit(10))]
    system = {'version': current_app.config['APP_VERSION'], 'environment': current_app.config['APP_ENV']}
    if wants_json():
        return jsonify({'counts': counts, 'events': latest, 'system': system})
    return render_template('super_admin/dashboard.html', counts=counts, events=latest, system=system)


@bp.get('/users')
def users():
    query = select(User)
    search = request.args.get('q', '').strip()[:255]
    if search:
        query = query.where(or_(User.name.ilike('%' + search + '%'), User.email.ilike('%' + search + '%')))
    role = request.args.get('role', '')
    if role:
        if role not in ROLES:
            raise AdminError('Invalid role filter.')
        query = query.where(User.role == role)
    status = request.args.get('status', '')
    if status not in {'', 'active', 'inactive', 'deleted'}:
        raise AdminError('Invalid status filter.')
    if status == 'deleted':
        query = query.where(User.deleted_at.is_not(None))
    elif request.args.get('include_deleted') != '1':
        query = query.where(User.deleted_at.is_(None))
    if status in {'active', 'inactive'}:
        query = query.where(User.is_active.is_(status == 'active'))
    sort = request.args.get('sort', 'name')
    direction = request.args.get('direction', 'asc')
    columns = {'name': User.name, 'email': User.email, 'role': User.role, 'created_at': User.created_at, 'last_login_at': User.last_login_at}
    if sort not in columns or direction not in {'asc', 'desc'}:
        raise AdminError('Invalid sort option.')
    query = query.order_by(getattr(columns[sort], direction)(), User.id.asc())
    with get_session() as db:
        items, pagination = paginated(db, query)
        results = [snapshot(user) for user in items]
        from companies.models import Company
        owner_ids = set(db.scalars(select(Company.owner_user_id).where(Company.owner_user_id.in_([user.id for user in items])))) if items else set()
        for result in results: result['has_company'] = result['id'] in owner_ids
    if wants_json():
        return jsonify({'users': results, 'pagination': pagination})
    return render_template('super_admin/users.html', users=results, pagination=pagination)


@bp.get('/users/new')
def create_form():
    return render_template('super_admin/user_form.html', user=None)


@bp.route('/users/new', methods=['POST'])
def create_user():
    result, password = mutate(g.super_identity.id, 'user.create', payload(), ip=request.remote_addr, expected_epoch=session.get('session_epoch', 0))
    if wants_json():
        response = {'user': result}
        if password:
            response['temporary_password'] = password
        return jsonify(response), 201
    return render_template('super_admin/saved.html', user=result, temporary_password=password), 201


@bp.get('/users/<int:user_id>')
def user_detail(user_id):
    with get_session() as db:
        user = db.get(User, user_id)
        if not user:
            abort(404)
        result = snapshot(user)
        events, pagination = paginated(db, select(UserAuditEvent).where(UserAuditEvent.target_id == user_id).order_by(UserAuditEvent.changed_at.desc(), UserAuditEvent.id.desc()))
        entries = [entry.to_dict() for entry in events]
    if wants_json():
        return jsonify({'user': result, 'events': entries, 'pagination': pagination})
    return render_template('super_admin/user_detail.html', user=result, events=entries, pagination=pagination)


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST', 'PUT'])
def edit_user(user_id):
    if request.method == 'GET':
        with get_session() as db:
            user = db.get(User, user_id)
            if not user:
                abort(404)
            if user.deleted_at:
                raise AdminError('Restore the deleted user before editing it.', 409)
            result = snapshot(user)
        return render_template('super_admin/user_form.html', user=result)
    return change_user(user_id, 'user.edit')


def change_user(user_id, action):
    result, password = mutate(g.super_identity.id, action, payload(), user_id, request.remote_addr, expected_epoch=session.get('session_epoch', 0))
    if wants_json():
        response = {'user': result}
        if password:
            response['temporary_password'] = password
        return jsonify(response)
    if password:
        return render_template('super_admin/saved.html', user=result, temporary_password=password)
    flash('تم حفظ التغيير وتسجيله في سجل التدقيق.', 'success')
    return redirect(url_for('super_admin.user_detail', user_id=user_id))


@bp.route('/users/<int:user_id>/status', methods=['POST', 'PUT'])
def set_status(user_id):
    data = payload()
    if not isinstance(data.get('action'), str) or data.get('action') not in {'activate', 'deactivate'}:
        raise AdminError('Choose activate or deactivate.')
    return change_user(user_id, 'user.' + data['action'])


@bp.route('/users/<int:user_id>/password', methods=['POST', 'PUT'])
def reset_password(user_id):
    return change_user(user_id, 'user.password_reset')


@bp.route('/users/<int:user_id>/delete', methods=['POST', 'DELETE'])
def soft_delete(user_id):
    return change_user(user_id, 'user.soft_delete')


@bp.route('/users/<int:user_id>/restore', methods=['POST'])
def restore_user(user_id):
    return change_user(user_id, 'user.restore')


@bp.get('/audit')
def audit_log():
    query = select(UserAuditEvent)
    actor = request.args.get('actor', '')
    if actor:
        try:
            actor_id = int(actor)
        except ValueError as error:
            raise AdminError('Invalid actor filter.') from error
        query = query.where(UserAuditEvent.actor_id == actor_id)
    action = request.args.get('action', '')
    if action:
        if action not in ACTIONS:
            raise AdminError('Invalid action filter.')
        query = query.where(UserAuditEvent.action == action)
    for key, inclusive in [('from', True), ('to', False)]:
        value = request.args.get(key, '')
        if value:
            try:
                date = datetime.strptime(value, '%Y-%m-%d')
            except ValueError as error:
                raise AdminError('Dates must use YYYY-MM-DD.') from error
            query = query.where(UserAuditEvent.changed_at >= date) if inclusive else query.where(UserAuditEvent.changed_at < date + timedelta(days=1))
    query = query.order_by(UserAuditEvent.changed_at.desc(), UserAuditEvent.id.desc())
    with get_session() as db:
        items, pagination = paginated(db, query)
        entries = [item.to_dict() for item in items]
        actors = [snapshot(user) for user in db.scalars(select(User).order_by(User.name))]
    if wants_json():
        return jsonify({'events': entries, 'pagination': pagination})
    return render_template('super_admin/audit.html', events=entries, actors=actors, actions=ACTIONS, pagination=pagination)


@bp.route('/settings', methods=['GET', 'POST', 'PUT'])
def settings():
    if request.method != 'GET':
        result, unused = mutate(g.super_identity.id, 'registration.toggle', payload(), ip=request.remote_addr, expected_epoch=session.get('session_epoch', 0))
        if wants_json():
            return jsonify(result)
        flash('تم تحديث إعداد التسجيل وتسجيل التغيير.', 'success')
        return redirect(url_for('super_admin.settings'))
    enabled = registration_enabled()
    from .models import PlatformSetting
    with get_session() as db:
        setting = db.get(PlatformSetting, 'max_companies_per_user')
        maximum = setting.integer_value if setting and setting.integer_value is not None else 1
    if wants_json():
        return jsonify({'public_registration_enabled': enabled, 'max_companies_per_user': maximum})
    return render_template('super_admin/settings.html', enabled=enabled, maximum=maximum)
