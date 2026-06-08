"""
Composition root of this application.
"""
from __future__ import annotations

from pathlib import Path

from modules.catalog.application.services.book_service import BookService
from modules.catalog.domain.book import Book
from modules.catalog.infra.repositories.duckdb_book_repository import (
    DuckDBBookRepository,
)
from modules.borrowing.application.services.loan_service import LoanService
from modules.borrowing.domain.loan_repository import LoanRepository
from modules.borrowing.domain.loan import Loan, LoanStatus, LoanError
from modules.borrowing.infra.repositories.duckdb_loan_repository import (
    DuckDBLoanRepository,
)


def main() -> None:
    """Main entry point."""
    import duckdb
    from datetime import datetime
    from uuid import uuid4
    from click.testing import CliRunner

    runner = CliRunner()

    # Use DuckDBBookRepository
    book_db_path = Path(__file__).parent / "assets" / "books.db"
    book_db_path.parent.mkdir(exist_ok=True)
    book_repo = DuckDBBookRepository(str(book_db_path))
    
    # Add some test books
    book1 = Book(
        id="ISBN-1234567890",
        title="Book Title",
        author="John Doe",
        isbn="ISBN-1234567890",
        total_copies=3,
        available_copies=3,
    )
    book2 = Book(
        id="ISBN-0987654321",
        title="Another Book",
        author="Jane Doe",
        isbn="ISBN-0987654321",
        total_copies=2,
        available_copies=2,
    )
    book_repo.save(book1)
    book_repo.save(book2)
    books = book_repo.find_all()
    print(f"Book repository has {len(books)} books")

    # Test book service
    book_service = BookService(book_repo)
    book = book_service.get_book("ISBN-1234567890")
    print(f"Book: {book}")

    # Test loan service
    loan_db_path = Path(__file__).parent / "assets" / "loans.db"
    loan_repo = DuckDBLoanRepository(str(loan_db_path))
    loan_service = LoanService(loan_repo, book_repo)
    try:
        new_loan = loan_service.borrow_book(
            {
                "id": "L001",
                "book_id": "ISBN-1234567890",
                "borrower_name": "Bob",
            }
        )
        print(f"New loan: {new_loan}")
    except Exception as e:
        print(f"Borrow error: {e}")

    # List all loans
    loans = loan_repo.list_all()
    print(f"Loans: {loans}")


if __name__ == "__main__":
    main()
