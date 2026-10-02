import pytest

from app import create_app
from database import get_session
from models.client import Client


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.test_client() as client:
        yield client


def login(client):
    response = client.post('/login', json={'email': 'admin@example.com', 'password': 'Admin123!'})
    assert response.status_code == 200
    return response.get_json()['csrf_token']


def test_login_and_invoice_creation(client):
    token = login(client)
    response = client.post('/clients', json={'name': 'Acme Ltd', 'email': 'hello@acme.test'}, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    client_id = response.get_json()['client']['id']
    response = client.post('/invoices', json={'client_id': client_id, 'tax_rate': 10, 'items': [{'description': 'Design', 'quantity': 2, 'unit_price': 100}]}, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    invoice = response.get_json()['invoice']
    assert invoice['invoice_number'].startswith('INV-')
    assert invoice['subtotal'] == 200.0
    assert invoice['tax_amount'] == 20.0
    assert invoice['total'] == 220.0


def test_csrf_is_required(client):
    login(client)
    assert client.post('/clients', json={'name': 'Blocked'}).status_code == 400
