"""Local Windows/Linux development only. Original application source is not patched."""
import argparse
import getpass
import importlib.util
import os
import secrets
import sys
from pathlib import Path

from werkzeug.serving import run_simple
from accounting_entrypoint import preflight

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTING_PREFIXES = frozenset({'login', 'logout', 'register', 'me', 'users', 'clients', 'invoices', 'invoice', 'dashboard', 'static', 'super-admin', 'companies'})


class SameOriginApplications:
    def __init__(self, portfolio, accounting):
        self.portfolio = portfolio
        self.accounting = accounting

    def __call__(self, environ, start_response):
        first = environ.get('PATH_INFO', '/').lstrip('/').split('/', 1)[0]
        application = self.accounting if first in ACCOUNTING_PREFIXES else self.portfolio
        # Do not strip paths or add SCRIPT_NAME: the frozen app uses absolute routes.
        return application(environ, start_response)


def load_application(name, folder):
    spec = importlib.util.spec_from_file_location(name, folder / 'app.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module.app


def build_application(database, demo=False):
    database = database.expanduser().resolve()
    if not database.is_file() and not demo:
        raise RuntimeError('Existing database not found. Supply --database, or explicitly use --demo for a new disposable local database.')
    new_demo = not database.is_file() and demo
    if new_demo:
        database.parent.mkdir(parents=True, exist_ok=True)
        password = getpass.getpass('Choose a local demo administrator password (12+ characters): ')
        if len(password) < 12:
            raise RuntimeError('Demo administrator password must have at least 12 characters.')
        os.environ['ADMIN_PASSWORD'] = password
    else:
        os.environ.setdefault('ADMIN_PASSWORD', secrets.token_urlsafe(24))
    os.environ.setdefault('SECRET_KEY', secrets.token_hex(32))
    os.environ['DATABASE_URL'] = 'sqlite:///' + database.as_posix()
    if not new_demo:
        preflight()  # Refuse known schema/backfill/seed changes to an existing file.
    accounting = load_application('_eid_accounting_local', ROOT / 'accounting-software')
    portfolio = load_application('_eid_portfolio_local', ROOT / 'portfolio')
    return SameOriginApplications(portfolio, accounting)


def main():
    parser = argparse.ArgumentParser(description='One-origin local portfolio + original accounting app. Not a production server.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--database', type=Path, help='Your existing compatible SQLite file; never committed or copied by this launcher.')
    group.add_argument('--demo', action='store_true', help='Explicitly create/reuse ignored runtime/local-demo.db, separate from any real database.')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    database = ROOT / 'runtime/local-demo.db' if args.demo else args.database
    try:
        application = build_application(database, demo=args.demo)
    except (RuntimeError, ValueError) as error:
        parser.exit(1, 'Startup refused: ' + str(error) + '\n')
    print(f'Arabic portfolio: http://127.0.0.1:{args.port}/', flush=True)
    print(f'Original accounting login: http://127.0.0.1:{args.port}/login', flush=True)
    if args.demo:
        print('Local demonstration only. Login email: admin@example.com. Use the password you chose when creating this demo.', flush=True)
    else:
        print('Using the existing database and existing login credentials; no password rotation performed.', flush=True)
    run_simple('127.0.0.1', args.port, application, threaded=True, use_reloader=False, use_debugger=False)


if __name__ == '__main__':
    main()
