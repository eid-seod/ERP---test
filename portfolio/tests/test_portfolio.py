from html.parser import HTMLParser

import pytest

from app import create_app, DEFAULT_SOFTWARE_URL


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


@pytest.fixture()
def client():
    return create_app({'TESTING': True}).test_client()


def test_personal_homepage_content(client):
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for text in ['Eid Saeed', 'Mahmoud', 'Accounts Manager', 'Finance Professional', 'Accounting Systems Specialist',
                 'ABOUT ME', 'PROFESSIONAL EXPERIENCE', 'PROFESSIONAL SERVICES', 'PROJECTS', 'CONTACT',
                 'Remote Accounting', 'Financial Management', 'Odoo', 'Zoho Books', 'Open Software', '01000062838']:
        assert text in html
    assert 'not a separate company' in html
    assert 'does not send or store' in html
    assert 'tel:01000062838' in html


def test_software_is_external_link_only(client):
    collector = LinkCollector()
    collector.feed(client.get('/').get_data(as_text=True))
    software_links = [link for link in collector.links if 'software-link' in link.get('class', '')]
    assert len(software_links) == 1
    assert software_links[0]['href'] == DEFAULT_SOFTWARE_URL
    assert software_links[0]['target'] == '_blank'
    assert 'noopener' in software_links[0]['rel']
    for route in ['/login', '/dashboard', '/invoices', '/clients', '/app']:
        assert client.get(route).status_code == 404
    assert client.post('/').status_code == 405


def test_route_manifest_and_health(client):
    assert client.get('/manus-routes.json').get_json()['routes'] == [
        {'path': '/', 'title': 'Eid Saeed Mahmoud — Professional Portfolio'}
    ]
    assert client.get('/health').get_json()['status'] == 'ok'
    for file in ['/static/css/portfolio.css', '/static/js/portfolio.js', '/static/images/accounting-dashboard.png', '/static/images/accounting-invoice.png']:
        assert client.get(file).status_code == 200


def test_bad_links_are_rejected():
    for value in ['javascript:alert(1)', '//example.com', 'https://user:password@example.com']:
        with pytest.raises(ValueError):
            create_app({'SOFTWARE_URL': value})


def test_missing_page_and_no_guessed_domain(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert 'noindex' in response.get_data(as_text=True)
    html = client.get('/').get_data(as_text=True)
    assert 'rel="canonical"' not in html
    assert 'mailto:' not in html
    assert 'wa.me/' not in html
    assert client.get('/').headers['X-Content-Type-Options'] == 'nosniff'


def test_configured_public_origin():
    app = create_app({'TESTING': True, 'PUBLIC_ORIGIN': 'https://portfolio.example.org', 'SOFTWARE_URL': 'https://software.example.org/login'})
    html = app.test_client().get('/').get_data(as_text=True)
    assert 'href="https://portfolio.example.org/"' in html
    assert 'href="https://software.example.org/login"' in html
    assert 'Currently opens the existing temporary' not in html
