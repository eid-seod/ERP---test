"""Versioned migrations for isolated company SQLite databases."""
from .version001 import VERSION, upgrade

__all__ = ["VERSION", "upgrade"]
