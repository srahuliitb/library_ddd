"""Borrowing infrastructure layer - repository implementations."""
from .repositories.duckdb_loan_repository import DuckDBLoanRepository

__all__ = ["DuckDBLoanRepository"]
