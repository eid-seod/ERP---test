import os

import click
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from database import get_session
from models.user import User
from .service import AdminError, audit, profile, snapshot


def register_cli(app):
    @app.cli.command('create-super-admin')
    def create_super_admin():
        """Bootstrap the FIRST Super Admin. No password is printed or hardcoded."""
        email = os.getenv('SUPER_ADMIN_EMAIL') or click.prompt('Email')
        name = os.getenv('SUPER_ADMIN_NAME') or email.partition('@')[0]
        password = os.getenv('SUPER_ADMIN_PASSWORD') or click.prompt('Password', hide_input=True, confirmation_prompt=True)
        try:
            name, email, role = profile({'name': name, 'email': email, 'role': 'super_admin', 'password': password}, require_password=True)
            with get_session() as db:
                db.execute(text('BEGIN IMMEDIATE'))
                if db.scalar(select(func.count(User.id)).where(User.role == 'super_admin')):
                    raise click.ClickException('A Super Admin already exists; use the authenticated Super Admin area.')
                user = User(name=name, email=email, role=role)
                user.set_password(password)
                db.add(user)
                db.flush()
                audit(db, user, 'super_admin.bootstrap', user, after=snapshot(user))
                db.commit()
            click.echo('First Super Admin created. Sign in through the existing /login page. Password was not printed.')
        except AdminError as error:
            raise click.ClickException(str(error)) from error
        except IntegrityError as error:
            raise click.ClickException('Email already exists; no existing account was promoted or changed.') from error
