"""
Composition root of this application.

This is the ONLY place that knows about every layer of every bounded context.
It creates concrete implementations and wires them together. No other file
imports infrastructure directly - they receive pre-wired services instead.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

# --- Catalog bounded context ---
from modules.catalog.infrastructure.repositories.duckdb_book_repository import DuckDBBookRepository
from modules.catalog.application.services.book_service_impl import BookService
from modules.catalog.interface.routes import catalog_router

# --- Borrowing bounded context ---
from modules.borrowing.infrastructure.repositories.duckdb_loan_repository import DuckDBLoanRepository
from modules.borrowing.application.services.loan_service_impl import LoanService
from modules.borrowing.interface.routes import borrowing_router


def build_app() -> FastAPI:
    """Wires up all the bounded contexts and returns a ready-to-run FastAPI app."""
    app = FastAPI(title="Library DDD API", version="1.0.0")

    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # --- Catalog bounded context ---
    book_repo = DuckDBBookRepository(str(data_dir / "catalog.parquet"))
    book_service = BookService(book_repo)
    app.include_router(catalog_router(book_service), prefix="/catalog")

    # --- Borrowing bounded context ---
    loan_repo = DuckDBLoanRepository(str(data_dir / "borrowing.parquet"))
    # Cross-context dependency: inject the catalog service into borrowing
    loan_service = LoanService(loan_repo, book_service)
    app.include_router(borrowing_router(loan_service), prefix="/borrowing")

    @app.get("/")
    async def root():
        return {
            "message": "Library DDD API",
            "contexts": ["catalog", "borrowing"],
            "docs": "/docs",
        }

    return app