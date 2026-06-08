"""Catalog infrastructure layer - repository implementations."""
from .repositories.duckdb_book_repository import DuckDBBookRepository

__all__ = ["DuckDBBookRepository"]
