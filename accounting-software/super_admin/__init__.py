import os

from flask import g, jsonify, redirect, request, session

from migrations.super_admin import require_existing_upgrade
from . import models  # Register only user audit/settings metadata.
from .cli import register_cli
from .views import bp

VERSION = 'super-admin-step1'


def init_super_admin(app):
    app.config.setdefault('APP_VERSION', os.getenv('APP_VERSION', VERSION))
    app.config.setdefault('APP_ENV', os.getenv('APP_ENV', 'not configured'))
    app.register_blueprint(bp)
    register_cli(app)

    @app.before_request
    def validate_existing_session():
        from routes.auth import current_user
        had_session = bool(session.get('user_id'))
        g.super_identity = current_user()
        if had_session and not g.super_identity:
            session.clear()
            if request.path in {'/', '/login', '/register', '/logout'} or request.path.startswith('/static/'):
                return None
            if request.path.startswith(('/super-admin', '/dashboard', '/invoice/')):
                return redirect('/login')
            return jsonify({'error': 'Authentication required.'}), 401

    @app.context_processor
    def super_admin_context():
        return {'super_identity': g.get('super_identity')}
