import json
import secrets

from flask import current_app
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_session
from models.user import User
from .models import PlatformSetting, UserAuditEvent, utcnow

ROLES = ('user', 'admin', 'super_admin')
ACTIONS = ('user.create', 'user.edit', 'user.activate', 'user.deactivate', 'user.password_reset', 'user.soft_delete', 'user.restore', 'registration.toggle', 'auth.login', 'super_admin.bootstrap')
REGISTRATION = 'public_registration_enabled'


class AdminError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def snapshot(user):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role,
            'is_active': bool(user.is_active), 'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None}


def audit(db, actor, action, target=None, before=None, after=None, ip=None):
    # Callers use explicit public-field snapshots, never user.__dict__ or password values.
    db.add(UserAuditEvent(actor_id=actor.id, target_id=target.id if target else None,
        actor_name=actor.name, actor_email=actor.email, action=action,
        before_data=json.dumps(before or {}, ensure_ascii=False), after_data=json.dumps(after or {}, ensure_ascii=False),
        changed_at=utcnow(), ip_address=ip[:64] if ip else None))


def registration_enabled():
    with get_session() as db:
        row = db.get(PlatformSetting, REGISTRATION)
        return bool(row and row.value)


def record_login(db, user, ip):
    before = {'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None}
    user.last_login_at = utcnow()
    audit(db, user, 'auth.login', user, before, {'last_login_at': user.last_login_at.isoformat()}, ip)


def detach_legacy_deleted_user(db, user_id):
    # Preserve audit events when the pre-existing admin endpoint hard-deletes a normal user.
    db.execute(update(UserAuditEvent).where(UserAuditEvent.actor_id == user_id).values(actor_id=None))
    db.execute(update(UserAuditEvent).where(UserAuditEvent.target_id == user_id).values(target_id=None))


def actor_in_transaction(db, actor_id, expected_epoch=None):
    actor = db.get(User, actor_id)
    if not actor or actor.role != 'super_admin' or not actor.is_active or actor.deleted_at:
        raise AdminError('Super Admin access required.', 403)
    if expected_epoch is not None and actor.session_epoch != expected_epoch:
        raise AdminError('Authentication required.', 403)
    return actor


def protect(db, actor, target, new_role=None, new_active=None, deleting=False):
    losing_role = new_role is not None and new_role != 'super_admin'
    losing_active = new_active is False or deleting
    if target.role == 'super_admin' and target.is_active and not target.deleted_at and (losing_role or losing_active):
        count = db.scalar(select(func.count(User.id)).where(User.role == 'super_admin', User.is_active.is_(True), User.deleted_at.is_(None)))
        if count <= 1:
            raise AdminError('The last active Super Admin cannot be deactivated, deleted or demoted.', 409)
    if actor.id == target.id and (deleting or new_active is False or losing_role):
        raise AdminError('You cannot deactivate, delete or demote your own account.', 409)


def profile(data, require_password=False):
    from routes.auth import _validate_user
    errors, email = _validate_user(data, require_password=require_password)
    name = data.get('name', '').strip()
    role = data.get('role', 'user')
    if len(name) > 120 or len(email) > 255:
        errors.append('Name or email is too long.')
    if role not in ROLES:
        errors.append('Invalid role.')
    if errors:
        raise AdminError(' '.join(errors))
    return name, email, role


def mutate(actor_id, action, data, target_id=None, ip=None, expected_epoch=None):
    generated = None
    try:
        with get_session() as db:
            db.execute(text('BEGIN IMMEDIATE'))
            actor = actor_in_transaction(db, actor_id, expected_epoch)
            target = db.get(User, target_id) if target_id is not None else None
            if target_id is not None and not target:
                raise AdminError('User not found.', 404)
            if target and target.deleted_at and action != 'user.restore':
                raise AdminError('Restore the deleted user before changing it.', 409)
            before = snapshot(target) if target else {}
            if action == 'user.create':
                name, email, role = profile(data)
                password = data.get('password', '')
                if not password:
                    generated = password = secrets.token_urlsafe(18)
                if len(password) < 8:
                    raise AdminError('Password must be at least 8 characters.')
                target = User(name=name, email=email, role=role)
                target.set_password(password)
                db.add(target)
                db.flush()
            elif action == 'user.edit':
                name, email, role = profile({**data, 'role': data.get('role', target.role)})
                protect(db, actor, target, new_role=role)
                target.name, target.email = name, email
                if target.role != role:
                    target.session_epoch += 1
                target.role = role
            elif action in {'user.activate', 'user.deactivate'}:
                active = action == 'user.activate'
                protect(db, actor, target, new_active=active)
                target.is_active = active
                if not active:
                    target.session_epoch += 1
            elif action == 'user.password_reset':
                password = data.get('password', '')
                if not password:
                    generated = password = secrets.token_urlsafe(18)
                if len(password) < 8:
                    raise AdminError('Password must be at least 8 characters.')
                target.set_password(password)
                target.session_epoch += 1
                before = {}
            elif action == 'user.soft_delete':
                protect(db, actor, target, deleting=True)
                target.deleted_at, target.is_active = utcnow(), False
                target.session_epoch += 1
            elif action == 'user.restore':
                if not target.deleted_at:
                    raise AdminError('User is not deleted.', 409)
                target.deleted_at = None
                target.is_active = False  # Restore safely; activation is a separate audited action.
                target.session_epoch += 1
            elif action == 'registration.toggle':
                value = data.get('enabled')
                if isinstance(value, bool):
                    enabled = value
                elif isinstance(value, str) and value in {'1', 'true', 'on', '0', 'false', 'off'}:
                    enabled = value in {'1', 'true', 'on'}
                else:
                    raise AdminError('Choose a valid registration setting.')
                row = db.get(PlatformSetting, REGISTRATION)
                before = {REGISTRATION: bool(row and row.value)}
                if row is None:
                    row = PlatformSetting(key=REGISTRATION, value=enabled)
                    db.add(row)
                else:
                    row.value = enabled
                row.updated_at = utcnow()
                audit(db, actor, action, before=before, after={REGISTRATION: enabled}, ip=ip)
                db.commit()
                return {'public_registration_enabled': enabled}, None
            else:
                raise AdminError('Unknown action.')
            db.flush()
            after = {'password_reset': True} if action == 'user.password_reset' else snapshot(target)
            # Log only changed public fields. Reset has an occurrence marker, not a secret/hash.
            changes = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
            audit(db, actor, action, target,
                  {key: before.get(key) for key in changes}, {key: after.get(key) for key in changes}, ip)
            result = snapshot(target)
            db.commit()
            return result, generated
    except IntegrityError as error:
        raise AdminError('Email is already registered.', 409) from error
    except OperationalError as error:
        if 'locked' in str(error).lower():
            raise AdminError('Another administrative change is in progress; retry.', 409) from error
        raise
