"""
Borrowing domain entities - the stable core of the borrowing bounded context.

This file has ZERO imports from any other layer. It is the stable core:
everything else in the system depends on it, it depends on nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


class LoanNotFoundError(Exception):
    """Raised when a loan id does not exist."""


class LoanAlreadyReturnedError(Exception):
    """Raised when trying to return an already-returned loan."""


@dataclass
class Loan:
    """A loan aggregate - one borrower taking one book."""

    id: str
    book_id: str
    borrower_name: str
    borrowed_at: datetime = field(default_factory=datetime.utcnow)
    returned_at: datetime | None = None

    def is_active(self) -> bool:
        """Check if the loan is still active (not returned)."""
        return self.returned_at is None

    def validate(self) -> None:
        """Validate loan data."""
        if not self.id or not self.id.strip():
            raise ValueError("Loan id is required.")
        if not self.book_id or not self.book_id.strip():
            raise ValueError("book_id is required.")
        if not self.borrower_name or not self.borrower_name.strip():
            raise ValueError("borrower_name is required.")

    def standardize(self) -> None:
        """Normalize loan data before saving."""
        self.borrower_name = self.borrower_name.strip()

    def mark_returned(self) -> None:
        """Mark this loan as returned."""
        if not self.is_active():
            raise LoanAlreadyReturnedError(
                f"Loan {self.id!r} was already returned at {self.returned_at}."
            )
        self.returned_at = datetime.utcnow()
