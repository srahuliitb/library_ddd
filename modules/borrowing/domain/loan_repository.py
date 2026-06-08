"""
Abstract repository contract for the Borrowing bounded context.

This is the ONLY interface that the application layer uses to access loan data.
Infrastructure (DuckDB, in-memory, etc.) must implement this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .loan import Loan


class LoanRepository(ABC):
    """Abstract contract for persisting loans."""

    @abstractmethod
    def save(self, loan: Loan) -> None:
        """Save or update a loan."""
        ...

    @abstractmethod
    def get(self, loan_id: str) -> Loan:
        """Get a loan by id. Raises LoanNotFoundError if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[Loan]:
        """List all loans."""
        ...
