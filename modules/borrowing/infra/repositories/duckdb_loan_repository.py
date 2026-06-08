"""
DuckDB-backed implementation of LoanRepository.

Persists loans to a parquet file via DuckDB. Implements the abstract
LoanRepository interface from the domain layer. Imports from domain only.

This file is NEVER imported by application or interface layers - only by
composition_root.py.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import duckdb

from modules.borrowing.domain.loan import Loan, LoanNotFoundError, LoanError, LoanStatus
from modules.borrowing.domain.loan_repository import (
    LoanRepository,
    InMemoryLoanRepository,
)


class DuckDBLoanRepository(LoanRepository):
    """Concrete LoanRepository using DuckDB + parquet storage."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._con = duckdb.connect(":memory:")
        self._con.execute("DROP TABLE IF EXISTS loans")
        self._con.execute(
            """
            CREATE TABLE loans (
                id             VARCHAR PRIMARY KEY,
                book_id        VARCHAR,
                borrower_name  VARCHAR,
                borrowed_at    TIMESTAMP,
                returned_at    TIMESTAMP,
                status         VARCHAR
            )
            """
        )
        path = Path(db_path)
        if path.exists():
            self._con.execute(
                f"INSERT INTO loans SELECT * FROM read_parquet('{db_path}')"
            )

    def save(self, loan: Loan) -> None:
        # First check if active loan exists for this book
        cursor = self._con.execute(
            """
            SELECT id, borrower_name FROM loans
            WHERE book_id = ?
              AND status = 'ACTIVE'
              AND returned_at IS NULL
            """,
            [loan.book_id],
        )
        existing = cursor.fetchone()
        if existing is not None:
            raise LoanError(
                f"Book {loan.book_id} already on loan for borrower {existing[1]}"
            )
        else:
            # No active loan exists, so this is a new loan (or book has none)
            self._con.execute(
                """
                INSERT INTO loans (id, book_id, borrower_name, borrowed_at, returned_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    book_id = EXCLUDED.book_id,
                    borrower_name = EXCLUDED.borrower_name,
                    borrowed_at = EXCLUDED.borrowed_at,
                    returned_at = EXCLUDED.returned_at,
                    status = EXCLUDED.status
                """,
                [
                    loan.id,
                    loan.book_id,
                    loan.borrower_name,
                    loan.borrowed_at,
                    loan.returned_at,
                    loan.status,
                ],
            )

    def get(self, loan_id: str) -> Loan:
        row = self._con.execute(
            """
            SELECT id, book_id, borrower_name, borrowed_at, returned_at, status
            FROM loans
            WHERE id = ?
            """,
            [loan_id],
        ).fetchone()
        if row is None:
            raise LoanNotFoundError(loan_id)
        return Loan(
            id=row[0],
            book_id=row[1],
            borrower_name=row[2],
            borrowed_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            returned_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
            status=LoanStatus(row[5]),
        )

    def list_all(self) -> List[Loan]:
        cursor = self._con.execute(
            """
            SELECT id, book_id, borrower_name, borrowed_at, returned_at, status
            FROM loans
            ORDER BY borrowed_at DESC
            """
        )
        loans = []
        for row in cursor:
            loans.append(
                Loan(
                    id=row[0],
                    book_id=row[1],
                    borrower_name=row[2],
                    borrowed_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
                    returned_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
                    status=LoanStatus(row[5]),
                )
            )
        return loans

    def mark_returned(self, loan_id: str) -> None:
        """Mark a loan as returned."""
        self._con.execute(
            """
            UPDATE loans
            SET status = 'RETURNED', returned_at = ?
            WHERE id = ? AND status = 'ACTIVE'
            """,
            [datetime.now(), loan_id],
        )

    def _flush(self) -> None:
        self._con.execute(
            f"COPY loans TO '{self._db_path}' (FORMAT PARQUET)"
        )
