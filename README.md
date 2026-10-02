# Ledgerly — Flask Invoicing System

A polished, modular invoicing system built with **Flask**, **SQLAlchemy**, **SQLite**, and **vanilla JavaScript**.

## Features

- Session-based authentication with Werkzeug password hashing
- Admin and user roles; admin user management
- Per-session CSRF protection on all state-changing API routes
- SQLite database with `users`, `clients`, `invoices`, and `invoice_items` tables
- CRUD REST APIs for invoices and clients
- Automatic invoice numbering (`INV-YYYYMM-####`)
- Dynamic invoice line items, taxes, subtotals, and totals
- Responsive dashboard with invoice and client views
- Optional PDF export can be added on top of the invoice detail API

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

Default development admin: `admin@example.com` / `Admin123!`. Set `ADMIN_PASSWORD` and `SECRET_KEY` in production; the initial admin is created from `ADMIN_PASSWORD` on first database initialization.

## Tests

```bash
pytest -q
```

## API routes

- `POST /login`, `POST /logout`, `POST /register`, `GET /me`
- `GET /users`, `POST /users`, `PATCH /users/:id`, `DELETE /users/:id` (admin)
- `GET /clients`, `POST /clients`, `PATCH /clients/:id`, `DELETE /clients/:id`
- `GET /invoices`, `POST /invoices`, `GET /invoices/:id`, `PATCH /invoices/:id`, `DELETE /invoices/:id`

Use the `csrf_token` returned by `/login` or `/me` as the `X-CSRF-Token` header for mutations.

## Structure

```text
app.py                 Application factory and page routes
database.py            SQLAlchemy setup
models/                User, Client, Invoice, InvoiceItem ORM models
routes/                Auth, client, and invoice blueprints
templates/             Login, dashboard, and invoice form pages
static/                Responsive CSS and frontend JavaScript
tests/                 Flask smoke tests
```
