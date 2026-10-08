"""Read-only gate for existing platform financial schema; never upgrades it."""
from sqlalchemy import inspect
from models.client import Client
from models.invoice import Invoice, InvoiceItem, AuditTrail


def require_existing_business_schema(engine):
    with engine.connect() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        for model in (Client, Invoice, InvoiceItem, AuditTrail):
            table = model.__table__
            if table.name not in tables:
                raise RuntimeError('Existing platform financial schema needs explicit compatibility review; no automatic migration is allowed.')
            actual = {column['name'] for column in inspector.get_columns(table.name)}
            if not set(table.columns.keys()).issubset(actual):
                raise RuntimeError('Existing platform financial schema needs explicit compatibility review; no automatic migration is allowed.')
        if connection.exec_driver_sql('SELECT 1 FROM invoices WHERE updated_at IS NULL LIMIT 1').first() or connection.exec_driver_sql("SELECT 1 FROM invoice_items WHERE item_name='' LIMIT 1").first():
            raise RuntimeError('Existing platform requires an explicit legacy backfill review; startup did not change financial rows.')
