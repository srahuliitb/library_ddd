"""
Borrowing application service - the cross-context orchestrator.

This is where the two bounded contexts actually interact. The LoanService
uses the catalog's AbstractBookService to:
  - verify a book exists and is available before issuing a loan
  - decrement the catalog's available_copies when a loan is created
  - increment the catalog's available_copies when a loan is returned

It depends only on abstract types (LoanRepository and AbstractBookService),
so it can be unit tested by injecting fakes for both.
"""
from __future__ import annotations

from abc import ABC
from typing import List

from modules.borrowing.domain.loan import Loan, LoanNotFoundError, LoanAlreadyReturnedError
from modules.borrowing.domain.loan_repository import LoanRepository
from modules.catalog.domain.book import BookNotFoundError, BookUnavailableError
from modules.catalog.domain.book_service import AbstractBookService


class LoanService(ABC):
    """Use-case orchestrator for the borrowing context."""

    def __init__(
        self,
        loan_repo: LoanRepository,
        catalog_service: AbstractBookService,
    ) -> None:
        self._loan_repo = loan_repo
        self._catalog = catalog_service  # <- cross-context dependency

    def borrow_book(self, raw_data: dict) -> Loan:
        """
        Use case: a member borrows a book.

        Steps:
          1. Build + validate + standardize the loan entity.
          2. Verify the book exists in the catalog (cross-context call).
          3. Try to reserve a copy in the catalog (cross-context call).
          4. Persist the loan.
        """
        from datetime import datetime
        # borrowed_at defaults to now if not provided
        borrowed_at = raw_data.get("borrowed_at") or datetime.utcnow()
        loan = Loan(
            id=raw_data["id"],
            book_id=raw_data["book_id"],
            borrower_name=raw_data["borrower_name"],
            borrowed_at=borrowed_at,
        )
        loan.standardize()
        loan.validate()

        # Cross-context interaction #1: confirm the book exists.
        try:
            self._catalog.get_book(loan.book_id)
        except BookNotFoundError as exc:
            raise BookNotFoundError(
                f"Cannot create loan: {exc}"
            ) from exc

        # Cross-context interaction #2: reserve a copy.
        try:
            self._catalog.reserve_copy(loan.book_id)
        except BookUnavailableError as exc:
            raise BookUnavailableError(f"No available copies: {exc}") from exc

        self._loan_repo.save(loan)
        return loan

    def return_book(self, loan_id: str) -> Loan:
        """
        Use case: a member returns a borrowed book.

        Steps:
          1. Load the loan.
          2. Mark it as returned (domain rule).
          3. Release a copy back to the catalog (cross-context call).
          4. Persist the updated loan.
        """
        loan = self._loan_repo.get(loan_id)
        loan.mark_returned()

        # Cross-context interaction #3: release a copy.
        self._catalog.release_copy(loan.book_id)

        self._loan_repo.save(loan)
        return loan

    def list_loans(self) -> List[Loan]:
        """List all loans."""
        return self._loan_repo.list_all()

    def get_loan(self, loan_id: str) -> Loan:
        """Get a loan by id."""
        try:
            return self._loan_repo.get(loan_id)
        except LoanNotFoundError as exc:
            raise LoanNotFoundError(f"Loan {loan_id!r} not found.") from exc
