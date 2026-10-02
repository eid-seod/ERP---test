from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal = None


def configure_database(database_url: str):
    global _engine, _SessionLocal
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_engine(database_url, connect_args=connect_args, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session():
    if _SessionLocal is None:
        raise RuntimeError("Database has not been configured")
    return _SessionLocal()


@contextmanager
def session_scope():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _add_missing_columns(connection, table, columns):
    existing = {column["name"] for column in inspect(connection).get_columns(table)}
    for name, definition in columns.items():
        if name not in existing:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def init_db():
    from models.client import Client  # noqa: F401
    from models.invoice import AuditTrail, Invoice, InvoiceItem  # noqa: F401
    from models.user import User  # noqa: F401
    Base.metadata.create_all(_engine)
    if _engine.dialect.name != "sqlite":
        return
    with _engine.begin() as connection:
        _add_missing_columns(connection, "invoices", {
            "currency": "VARCHAR(3) NOT NULL DEFAULT 'USD'",
            "tds_enabled": "BOOLEAN NOT NULL DEFAULT 0",
            "tds_type": "VARCHAR(10) NOT NULL DEFAULT 'percent'",
            "tds_rate": "NUMERIC(12, 2) NOT NULL DEFAULT 0",
        })
        _add_missing_columns(connection, "invoice_items", {
            "item_code": "VARCHAR(80) NOT NULL DEFAULT ''",
            "item_name": "VARCHAR(200) NOT NULL DEFAULT ''",
            "discount": "NUMERIC(12, 2) NOT NULL DEFAULT 0",
            "tax_rate": "NUMERIC(5, 2) NOT NULL DEFAULT 0",
        })
        connection.execute(text("UPDATE invoice_items SET item_name = description WHERE item_name = ''"))
