"""
Smoke test: wires everything by hand (mimicking composition_root) and
exercises the cross-context interaction end-to-end.

This test does NOT import infrastructure from the application layer -
it only wires them in one place, exactly like composition_root does.
That mirrors the DDD rule: composition_root is the only place that
knows about both layers.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tempfile

from modules.catalog.infra.repositories.duckdb_book_repository import DuckDBBookRepository
from modules.catalog.application.services.book_service import BookService
from modules.borrowing.infra.repositories.duckdb_loan_repository import DuckDBLoanRepository
from modules.borrowing.application.services.loan_service import LoanService
from modules.catalog.domain.book import BookUnavailableError, BookNotFoundError
from modules.borrowing.domain.loan import NoAvailableCopiesError, LoanAlreadyReturnedError


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cat_path = str(Path(tmp) / "catalog.parquet")
        loan_path = str(Path(tmp) / "borrowing.parquet")

        # Wire the object graph (this is what composition_root does).
        cat_service = BookService(repo=DuckDBBookRepository(db_path=cat_path))
        loan_service = LoanService(
            loan_repo=DuckDBLoanRepository(db_path=loan_path),
            catalog_service=cat_service,
        )

        # 1. Add a book with 1 copy.
        cat_service.add_book({
            "id": "B001",
            "title": "Test Book",
            "author": "Tester",
            "isbn": "1234567890",
            "total_copies": 1,
        })
        book = cat_service.get_book("B001")
        assert book.available_copies == 1, "should start with 1 available copy"

        # 2. First loan succeeds and decrements catalog.
        loan_service.borrow_book(
            {"id": "L001", "book_id": "B001", "borrower_name": "Alice"}
        )
        book = cat_service.get_book("B001")
        assert book.available_copies == 0, "catalog should reflect the loan"

        # 3. Second loan fails because catalog reports no availability.
        try:
            loan_service.borrow_book(
                {"id": "L002", "book_id": "B001", "borrower_name": "Bob"}
            )
        except NoAvailableCopiesError:
            print("  ok: second borrow rejected (NoAvailableCopiesError)")
        else:
            raise AssertionError("expected NoAvailableCopiesError")

        # 4. Returning a non-existent book id fails at catalog level.
        try:
            loan_service.borrow_book(
                {"id": "L003", "book_id": "B999", "borrower_name": "Carol"}
            )
        except BookNotFoundError:
            print("  ok: borrow of unknown book rejected (BookNotFoundError)")
        else:
            raise AssertionError("expected BookNotFoundError")

        # 5. Return the book -> catalog copy count goes back up.
        loan_service.return_book("L001")
        book = cat_service.get_book("B001")
        assert book.available_copies == 1, "catalog should reflect the return"

        # 6. Cannot return the same loan twice.
        try:
            loan_service.return_book("L001")
        except LoanAlreadyReturnedError:
            print("  ok: double-return rejected (LoanAlreadyReturnedError)")
        else:
            raise AssertionError("expected LoanAlreadyReturnedError")

        # 7. List loans shows the history.
        loans = loan_service.list_loans()
        assert len(loans) == 1 and loans[0].returned_at is not None
        print(f"  ok: loan history recorded, {len(loans)} loan(s) total")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
