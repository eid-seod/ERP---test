from pathlib import Path

import pytest
from werkzeug.test import Client
from werkzeug.wrappers import Response

from run_local import SameOriginApplications, build_application


def endpoint(label):
    def application(environ, start_response):
        return Response(label + ':' + environ['PATH_INFO'])(environ, start_response)
    return application


@pytest.mark.parametrize('path', ['/', '/blog/cash-flow-planning', '/portfolio-assets/css/portfolio.css', '/shared-assets/fonts/tajawal-400-0.ttf'])
def test_public_routes_go_to_portfolio(path):
    client = Client(SameOriginApplications(endpoint('portfolio'), endpoint('accounting')), Response)
    assert client.get(path).text == 'portfolio:' + path


@pytest.mark.parametrize('path', ['/login', '/dashboard', '/invoices/7/pdf', '/invoice/7/edit', '/clients', '/users', '/static/js/app.js', '/super-admin', '/super-admin/users', '/super-admin/audit', '/super-admin/settings'])
def test_original_accounting_paths_are_not_rewritten(path):
    client = Client(SameOriginApplications(endpoint('portfolio'), endpoint('accounting')), Response)
    assert client.get(path).text == 'accounting:' + path


def test_missing_real_database_is_not_created(tmp_path):
    file = tmp_path / 'existing-but-missing.db'
    with pytest.raises(RuntimeError, match='Existing database not found'):
        build_application(file, demo=False)
    assert not file.exists()
