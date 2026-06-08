from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List

import duckdb

__all__ = ["LoanRepository", "InMemoryLoanRepository", "DatabaseLoanRepository"]


class LoanNotFoundError(Exception):
    """Raised when loan not found."""

    def __init__(self, loan_id: str):
        super().__init__(f"Loan '{loan_id}' not found")
        self.loan_id = loan_id


class LoanRepository(ABC):
    """
    Abstract contract for persisting loans.
    """

    @abstractmethod
    def save(self, loan: "Loan") -> None:
        ...

    @abstractmethod
    def get(self, loan_id: str) -> "Loan":
        ...

    @abstractmethod
    def list_all(self) -> List["Loan"]:
        ...


class InMemoryLoanRepository(LoanRepository):
    """
    In-memory implementation of LoanRepository for tests.
    """

    def __init__(self) -> None:
        self._store: dict[str, "Loan"] = {}

    def save(self, loan: "Loan") -> None:
        self._store[loan.id] = loan

    def get(self, loan_id: str) -> "Loan":
        try:
            return self._store[loan_id]
        except KeyError:
            raise LoanNotFoundError(loan_id)

    def list_all(self) -> List["Loan"]:
        return list(self._store.values())


class DatabaseLoanRepository(LoanRepository):
    """
    Database-backed implementation of LoanRepository.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._con = duckdb.connect(str(self._db_path))
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
        self._create_active_view()

    def _create_active_view(self) -> None:
        """Create active_loans view."""
        self._con.execute(
            """
            DROP VIEW IF EXISTS active_loans;
            CREATE VIEW active_loans AS
            SELECT * FROM loans
            WHERE status = 'ACTIVE' AND returned_at IS NULL
            """
        )

    def save(self, loan: "Loan") -> None:
        if loan.id in self._store_active_loans():
            raise LoanError(
                f"Active loan exists for book {loan.book_id} "
                f"with borrower {self._get_active_borrower(loan.book_id)}"
            )
        self._con.execute(
            """
            INSERT INTO loans (id, book_id, borrower_name, borrowed_at, returned_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
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
        self._create_active_view()

    def get(self, loan_id: str) -> "Loan":
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
        return Loan.from_row(row)

    def list_all(self) -> List["Loan"]:
        cursor = self._con.execute(
            """
            SELECT id, book_id, borrower_name, borrowed_at, returned_at, status
            FROM loans
            ORDER BY borrowed_at DESC
            """
        )
        loans = []
        for row in cursor:
            loans.append(Loan.from_row(row))
        return loans

    def _store_active_loans(self) -> dict[str, "Loan"]:
        cursor = self._con.execute(
            """
            SELECT id, book_id, borrower_name, borrowed_at, returned_at, status
            FROM loans
            WHERE status = 'ACTIVE' AND returned_at IS NULL
            """
        )
        loans = []
        for row in cursor:
            loans.append(Loan.from_row(row))
        return {loan.id: loan for loan in loans}

    def _get_active_borrower(self, book_id: str) -> str:
        row = self._con.execute(
            """
            SELECT borrower_name
            FROM loans
            WHERE book_id = ?
              AND status = 'ACTIVE'
              AND returned_at IS NULL
            """,
            [book_id],
        ).fetchone()
        if row is None:
            return "no active loan"
        return row[0]

    def mark_returned(self, loan_id: str) -> None:
        """Mark a loan as returned."""
        self._con.execute(
            """
            UPDATE loans
            SET status = 'RETURNED', returned_at = NOW()
            WHERE id = ? AND status = 'ACTIVE'
            """,
            [loan_id],
        )
        self._create_active_view()

    def mark_active(self, loan_id: str) -> None:
        """Mark a loan as active (re-activate)."""
        self._con.execute(
            """
            UPDATE loans
            SET status = 'ACTIVE'
            WHERE id = ? AND status = 'RETURNED'
            """,
            [loan_id],
        )
        self._create_active_view()
