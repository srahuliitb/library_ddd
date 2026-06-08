"""
Composition root - this file re-exports key types for internal convenience.

The actual FastAPI app builder lives in app/composition_root.py.
This file exists for backwards compatibility with seed_demo_data.py.
"""
from __future__ import annotations

from pathlib import Path

# Data paths (shared between contexts)
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

CATALOG_DB_PATH = str(DATA_DIR / "catalog.parquet")
BORROWING_DB_PATH = str(DATA_DIR / "borrowing.parquet")

# Re-export catalog components
from modules.catalog.infrastructure.repositories.duckdb_book_repository import (
    DuckDBBookRepository,
)
from modules.catalog.application.services.book_service_impl import BookService
from modules.catalog.domain.book import Book

# Re-export borrowing components
from modules.borrowing.infra.repositories.duckdb_loan_repository import (
    DuckDBLoanRepository,
)
from modules.borrowing.application.services.loan_service import LoanService
