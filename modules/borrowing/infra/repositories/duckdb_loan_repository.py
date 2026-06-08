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

from modules.borrowing.domain.loan import Loan, LoanNotFoundError
from modules.borrowing.domain.loan_repository import LoanRepository


class DuckDBLoanRepository(LoanRepository):
    """Concrete LoanRepository using DuckDB + parquet storage."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._con = duckdb.connect(database=":memory:")
        self._con.execute("DROP TABLE IF EXISTS loans")
        self._con.execute(
            """
            CREATE TABLE loans (
                id             VARCHAR PRIMARY KEY,
                book_id        VARCHAR,
                borrower_name  VARCHAR,
                borrowed_at    TIMESTAMP,
                returned_at    TIMESTAMP
            )
            """
        )
        path = Path(db_path)
        if path.exists() and path.stat().st_size > 0:
            self._con.execute(
                f"INSERT INTO loans SELECT * FROM read_parquet('{db_path}')"
            )

    def save(self, loan: Loan) -> None:
        self._con.execute(
            """
            INSERT INTO loans (id, book_id, borrower_name, borrowed_at, returned_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                book_id = EXCLUDED.book_id,
                borrower_name = EXCLUDED.borrower_name,
                borrowed_at = EXCLUDED.borrowed_at,
                returned_at = EXCLUDED.returned_at
            """,
            [
                loan.id,
                loan.book_id,
                loan.borrower_name,
                loan.borrowed_at,
                loan.returned_at,
            ],
        )
        self._flush()

    def get(self, loan_id: str) -> Loan:
        row = self._con.execute(
            "SELECT id, book_id, borrower_name, borrowed_at, returned_at "
            "FROM loans WHERE id = ?",
            [loan_id],
        ).fetchone()
        if row is None:
            raise LoanNotFoundError(loan_id)
        return self._row_to_loan(row)

    def list_all(self) -> List[Loan]:
        cursor = self._con.execute(
            "SELECT id, book_id, borrower_name, borrowed_at, returned_at "
            "FROM loans ORDER BY borrowed_at DESC"
        )
        rows = cursor.fetchall()
        return [self._row_to_loan(row) for row in rows]

    def _row_to_loan(self, row) -> Loan:
        # Create loan - borrowed_at should always be present
        loan = Loan(
            id=row[0],
            book_id=row[1],
            borrower_name=row[2],
            borrowed_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            returned_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
        )
        return loan

    def _flush(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._con.execute(f"COPY loans TO '{self._db_path}' (FORMAT PARQUET)")
