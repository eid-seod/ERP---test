from html.parser import HTMLParser
import pytest
from app import create_app
from content import SERVICES, ARTICLES


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


@pytest.fixture()
def client():
    return create_app({'TESTING': True, 'PUBLIC_ORIGIN': ''}).test_client()


def test_arabic_personal_identity(client):
    response = client.get('/')
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'lang="ar" dir="rtl"' in html
    for value in ['عيد سعيد محمود', 'Eid Saeed Mahmoud', 'مدير حسابات', 'متخصص مالي', 'الخدمات المهنية', 'المدونة', '01000062838']:
        assert value in html
    assert 'tel:01000062838' in html


def test_all_requested_services(client):
    assert len(SERVICES) == 12
    html = client.get('/').get_data(as_text=True)
    for term in ['Accounting', 'Financial Reporting', 'Financial Statements', 'Bookkeeping', 'Budgeting', 'Forecasting', 'Cash Flow', 'Payroll', 'Tax', 'VAT', 'ERP Implementation', 'Odoo Implementation', 'Zoho Books Implementation']:
        assert term in html
    assert 'تقييم الوضع المالي وتحسينه' in html


def test_software_is_same_origin_not_recreated(client):
    parser = Links(); parser.feed(client.get('/').get_data(as_text=True))
    links = [link for link in parser.links if 'software-link' in link.get('class', '')]
    assert len(links) == 1
    assert links[0]['href'] == '/login'
    assert '<iframe' not in client.get('/').get_data(as_text=True)
    assert '<a href="/login">البرنامج المحاسبي</a>' in client.get('/').get_data(as_text=True)
    for route in ['/login', '/dashboard', '/invoices', '/clients']:
        assert client.get(route).status_code == 404  # Served by the accounting proxy, not this app.
    assert client.post('/').status_code == 405


def test_assets_separated(client):
    for path in ['/portfolio-assets/css/portfolio.css', '/portfolio-assets/js/portfolio.js', '/shared-assets/images/personal-monogram.svg', '/shared-assets/fonts/tajawal-400-0.ttf']:
        assert client.get(path).status_code == 200
    assert client.get('/static/css/app.css').status_code == 404
    assert client.get('/shared-assets/../../accounting-software/database.db').status_code == 404


def test_articles_and_not_found(client):
    for item in ARTICLES:
        response = client.get('/blog/' + item['slug'])
        assert response.status_code == 200
        assert item['title'] in response.get_data(as_text=True)
        assert 'lang="ar" dir="rtl"' in response.get_data(as_text=True)
    assert client.get('/blog/missing').status_code == 404
    assert 'noindex' in client.get('/missing').get_data(as_text=True)


def test_route_manifest_includes_combined_pages(client):
    routes = client.get('/manus-routes.json').get_json()['routes']
    paths = {item['path'] for item in routes}
    assert {'/', '/login', '/dashboard', '/invoice/new', '/invoice/:invoice_id/edit'}.issubset(paths)
    assert len([path for path in paths if path.startswith('/blog/')]) == 3
    assert client.get('/health').get_json()['status'] == 'ok'


def test_no_guessed_domain_and_honest_contact(client):
    html = client.get('/').get_data(as_text=True)
    assert 'rel="canonical"' not in html
    assert 'لا يرسل أو يخزن' in html
    assert 'mailto:' not in html and 'wa.me/' not in html
    assert client.get('/sitemap.xml').status_code == 503


def test_public_origin_and_sitemap():
    client = create_app({'TESTING': True, 'PUBLIC_ORIGIN': 'https://owner.example.test'}).test_client()
    assert 'href="https://owner.example.test/"' in client.get('/').get_data(as_text=True)
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert 'https://owner.example.test/blog/' in response.get_data(as_text=True)
    assert '/login' not in response.get_data(as_text=True)
    for value in ['javascript:alert(1)', 'https://user:pass@example.test', 'https://example.test/wrong-path']:
        with pytest.raises(ValueError):
            create_app({'PUBLIC_ORIGIN': value})


def test_bidi_filter_escapes_content():
    app = create_app({'TESTING': True})
    rendered = str(app.jinja_env.filters['terms']('<script>alert(1)</script> Accounting'))
    assert '<script>' not in rendered
    assert '&lt;' in rendered
    assert '<bdi dir="ltr" lang="en">Accounting</bdi>' in rendered
