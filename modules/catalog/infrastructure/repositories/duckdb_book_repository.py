"""
DuckDB-backed implementation of BookRepository.

Persists books to a parquet file via DuckDB. Implements the abstract
BookRepository interface from the domain layer. Imports from domain only.

This file is NEVER imported by application or interface layers - only by
composition_root.py.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import duckdb

from modules.catalog.domain.book import Book, BookNotFoundError
from modules.catalog.domain.book_repository import BookRepository


class DuckDBBookRepository(BookRepository):
    """Concrete BookRepository using DuckDB + parquet storage."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._con = duckdb.connect(database=":memory:")
        self._con.execute("DROP TABLE IF EXISTS books")
        self._con.execute(
            """
            CREATE TABLE books (
                id              VARCHAR PRIMARY KEY,
                title           VARCHAR,
                author          VARCHAR,
                isbn            VARCHAR,
                total_copies    INTEGER,
                available_copies INTEGER,
                created_at      TIMESTAMP
            )
            """
        )
        path = Path(db_path)
        if path.exists() and path.stat().st_size > 0:
            self._con.execute(
                f"INSERT INTO books SELECT * FROM read_parquet('{db_path}')"
            )

    def save(self, book: Book) -> None:
        self._con.execute(
            """
            INSERT INTO books (id, title, author, isbn, total_copies, available_copies, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                author = EXCLUDED.author,
                isbn = EXCLUDED.isbn,
                total_copies = EXCLUDED.total_copies,
                available_copies = EXCLUDED.available_copies,
                created_at = EXCLUDED.created_at
            """,
            [
                book.id,
                book.title,
                book.author,
                book.isbn,
                book.total_copies,
                book.available_copies,
                book.created_at,
            ],
        )
        self._flush()

    def get(self, book_id: str) -> Book:
        row = self._con.execute(
            "SELECT id, title, author, isbn, total_copies, available_copies, created_at "
            "FROM books WHERE id = ?",
            [book_id],
        ).fetchone()
        if row is None:
            raise BookNotFoundError(book_id)
        return self._row_to_book(row)

    def list_all(self) -> List[Book]:
        cursor = self._con.execute(
            "SELECT id, title, author, isbn, total_copies, available_copies, created_at "
            "FROM books ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        return [self._row_to_book(row) for row in rows]

    def exists(self, book_id: str) -> bool:
        row = self._con.execute(
            "SELECT 1 FROM books WHERE id = ?", [book_id]
        ).fetchone()
        return row is not None

    def _row_to_book(self, row) -> Book:
        # Create book with required fields, available_copies is computed in __post_init__
        book = Book(
            id=row[0],
            title=row[1],
            author=row[2],
            isbn=row[3],
            total_copies=row[4],
            created_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )
        # Override with stored value if different
        book.available_copies = row[5]
        return book

    def _flush(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._con.execute(f"COPY books TO '{self._db_path}' (FORMAT PARQUET)")
