"""
Seed the library with some demo data so the API is useful out of the box.

Run this once before exercising the API:
    python -m library_ddd.seed_demo_data

It uses the application services (not raw SQL) so it exercises the same
path the HTTP routes would. This is a convenient way to populate DuckDB
parquet files with realistic data.
"""
from __future__ import annotations

from pathlib import Path

# Data paths (shared between contexts)
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

CATALOG_DB_PATH = str(DATA_DIR / "catalog.parquet")
BORROWING_DB_PATH = str(DATA_DIR / "borrowing.parquet")

from modules.catalog.infrastructure.repositories.duckdb_book_repository import (
    DuckDBBookRepository,
)
from modules.catalog.application.services.book_service_impl import BookService
from modules.borrowing.infra.repositories.duckdb_loan_repository import (
    DuckDBLoanRepository,
)
from modules.borrowing.application.services.loan_service import LoanService


def seed() -> None:
    # Wipe previous demo data so seed is idempotent.
    for p in (CATALOG_DB_PATH, BORROWING_DB_PATH):
        if Path(p).exists():
            Path(p).unlink()

    catalog_repo = DuckDBBookRepository(db_path=CATALOG_DB_PATH)
    catalog_service = BookService(repo=catalog_repo)

    borrowing_repo = DuckDBLoanRepository(db_path=BORROWING_DB_PATH)
    loan_service = LoanService(
        loan_repo=borrowing_repo, catalog_service=catalog_service
    )

    demo_books = [
        {
            "id": "B001",
            "title": "Domain-Driven Design",
            "author": "Eric Evans",
            "isbn": "9780321125217",
            "total_copies": 3,
        },
        {
            "id": "B002",
            "title": "Clean Architecture",
            "author": "Robert C. Martin",
            "isbn": "9780134494166",
            "total_copies": 2,
        },
        {
            "id": "B003",
            "title": "Designing Data-Intensive Applications",
            "author": "Martin Kleppmann",
            "isbn": "9781449373320",
            "total_copies": 1,
        },
    ]
    for raw in demo_books:
        catalog_service.add_book(raw)
        print(f"  + catalog: added {raw['id']} '{raw['title']}'")

    # Demonstrate cross-context interaction: borrow two of the three DDD books.
    loan_service.borrow_book(
        {"id": "L001", "book_id": "B001", "borrower_name": "Alice"}
    )
    print("  + borrowing: Alice borrowed B001")

    loan_service.borrow_book(
        {"id": "L002", "book_id": "B001", "borrower_name": "Bob"}
    )
    print("  + borrowing: Bob   borrowed B001")

    print(f"\nCatalog DB : {CATALOG_DB_PATH}")
    print(f"Borrowing DB: {BORROWING_DB_PATH}")
    print("\nSeed complete. Run `python main.py` to start the API.")


if __name__ == "__main__":
    seed()
