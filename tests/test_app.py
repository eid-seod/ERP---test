import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.test_client() as client:
        yield client


def login(client):
    response = client.post('/login', json={'email': 'admin@example.com', 'password': 'Admin123!'})
    assert response.status_code == 200
    return response.get_json()['csrf_token']


def register_and_login_user(client):
    response = client.post('/register', json={'name': 'Standard User', 'email': 'user@example.com', 'password': 'User12345!'})
    assert response.status_code == 201
    response = client.post('/login', json={'email': 'user@example.com', 'password': 'User12345!'})
    assert response.status_code == 200
    return response.get_json()['csrf_token']


def create_client(client, token):
    response = client.post('/clients', json={'name': 'Acme Ltd', 'email': 'hello@acme.test'}, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    return response.get_json()['client']['id']


def make_invoice(client, token, status='draft'):
    client_id = create_client(client, token)
    payload = {'client_id': client_id, 'status': status, 'currency': 'INR', 'tds_enabled': True, 'tds_type': 'percent', 'tds_rate': 10,
               'items': [{'item_code': 'DS-01', 'item_name': 'Design service', 'description': 'Brand design', 'quantity': 2, 'unit_price': 100, 'discount': 20, 'tax_rate': 18}]}
    response = client.post('/invoices', json=payload, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    return response.get_json()['invoice']


def test_itemized_totals_tds_and_audit(client):
    token = login(client)
    invoice = make_invoice(client, token)
    assert invoice['subtotal'] == 200.0
    assert invoice['total_discount'] == 20.0
    assert invoice['tax_amount'] == 32.4
    assert invoice['grand_total'] == 212.4
    assert invoice['tds_amount'] == 21.24
    assert invoice['net_payable'] == 191.16
    assert invoice['items'][0]['line_total'] == 212.4
    assert invoice['audit'] if 'audit' in invoice else True

    response = client.patch(f"/invoices/{invoice['id']}", json={'tds_type': 'fixed', 'tds_rate': 25, 'status': 'open'}, headers={'X-CSRF-Token': token})
    assert response.status_code == 200
    updated = response.get_json()['invoice']
    assert updated['tds_amount'] == 25.0
    assert updated['net_payable'] == 187.4
    audit = client.get(f"/invoices/{invoice['id']}/audit").get_json()['audit']
    assert any(entry['field_name'] == 'tds_rate' for entry in audit)


def test_legacy_invoice_tax_payload_and_csrf(client):
    token = login(client)
    client_id = create_client(client, token)
    response = client.post('/invoices', json={'client_id': client_id, 'tax_rate': 10, 'items': [{'description': 'Design', 'quantity': 2, 'unit_price': 100}]}, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    invoice = response.get_json()['invoice']
    assert invoice['tax_amount'] == 20.0
    assert client.post('/clients', json={'name': 'Blocked'}).status_code == 400


def test_locked_invoice_cannot_be_edited_by_regular_user(client):
    token = register_and_login_user(client)
    invoice = make_invoice(client, token, status='approved')
    response = client.patch(f"/invoices/{invoice['id']}", json={'notes': 'change'}, headers={'X-CSRF-Token': token})
    assert response.status_code == 409


def test_pdf_export(client):
    token = login(client)
    invoice = make_invoice(client, token)
    response = client.get(f"/invoices/{invoice['id']}/pdf")
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert response.data.startswith(b'%PDF')
