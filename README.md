# Ledgerly — Flask Invoicing System

A modular invoicing system built with **Flask**, **SQLAlchemy**, **SQLite**, and **vanilla JavaScript**.

## Features

- Session-based authentication with Werkzeug password hashing
- Admin and user roles; admin user management
- Per-session CSRF protection on all state-changing API routes
- Migration-safe SQLite schema upgrades for existing installations
- Detailed invoice items: code, name, description, quantity, unit price, discount, tax, and line total
- Real-time subtotal, discount, tax, grand total, TDS, and net payable calculations
- TDS enabled/disabled per invoice, with percentage or fixed-amount configuration
- Draft/Open invoice editing with full field and item audit trail
- Locked Approved, Posted, Fully Paid, and Paid invoices; admins have special edit permission
- Multiple currencies: USD, EUR, GBP, INR, AED, CAD, AUD, and JPY
- Professional PDF export and browser print action
- RESTful CRUD APIs for invoices and clients
- Responsive dashboard and invoice review/edit interface
- Historical invoices keep their saved currency, rates, discounts, tax, and TDS configuration

## Quick start on Windows

From PowerShell, run these commands in the project folder:

```powershell
py -m pip install -r requirements.txt
py app.py
```

If the app is already installed and only PDF export is failing:

```powershell
py -m pip install reportlab
```

ReportLab is loaded only when PDF export is requested, so the application itself can still start without it. The PDF endpoint will return an installation message until ReportLab is installed.

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
- `GET /invoices/:id/audit` — invoice audit history
- `GET /invoices/:id/pdf` — professional PDF export

Use the `csrf_token` returned by `/login` or `/me` as the `X-CSRF-Token` header for mutations.

Invoice item payload example:

```json
{
  "item_code": "CONS-001",
  "item_name": "Consulting service",
  "description": "Monthly advisory services",
  "quantity": 2,
  "unit_price": 500,
  "discount": 25,
  "tax_rate": 18
}
```

Invoice-level TDS fields are `tds_enabled`, `tds_type` (`percent` or `fixed`), and `tds_rate`. New invoices should use `draft` or `open` while being edited. Statuses `approved`, `posted`, `fully_paid`, and `paid` are locked for standard users.

## Structure

```text
app.py                 Application factory and page routes
database.py            SQLAlchemy setup and SQLite schema upgrades
models/                User, Client, Invoice, InvoiceItem, AuditTrail
routes/                Auth, client, and invoice blueprints
templates/             Login, dashboard, and invoice form pages
static/                Responsive CSS and frontend JavaScript
tests/                 Flask feature and regression tests
```
