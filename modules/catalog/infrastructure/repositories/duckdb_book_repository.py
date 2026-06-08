"""
DuckDB-backed implementation of BookRepository.

Persists books to a parquet file via DuckDB. Implements the abstract
BookRepository interface from the domain layer. Imports from domain only.

This file is NEVER imported by application or interface layers - only by
composition_root.py.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import duckdb

from modules.catalog.domain.book import Book, BookNotFoundError


class DuckDBBookRepository:
    """Concrete BookRepository using DuckDB + parquet storage."""

    def __init__(self, db) -> None:
        self._con = duckdb