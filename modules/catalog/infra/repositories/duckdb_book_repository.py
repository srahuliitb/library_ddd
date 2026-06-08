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


class DuckDBBookRepository:
    """Concrete BookRepository using DuckDB + parquet storage."""

    def __init__(self, db_path: str) -> None:




        self._con = duckdb.connect(db_path)
        cursor = self._con.execute("DROP TABLE IF EXISTS books")
        cursor = self._con.execute(
            """
            CREATE TABLE books (
                id            VARCHAR PRIMARY KEY,
                title         VARCHAR,
                author        VARCHAR,
                isbn          VARCHAR,
                total_copies  INTEGER,
                available_copies INTEGER,
                created_at    TIMESTAMP
            )
            """
        )


































































    def save(self, book: Book) -> None:
        self._con.execute(
            """


            INSERT INTO books (id, title, author, isbn, total_copies, available_copies, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET






                title=excluded.title,
                author=excluded.author,
                isbn=excluded.isbn,
                total_copies=excluded.total_copies,
                available_copies=excluded.available_copies,
                created_at=excluded.created_at
            """,
            [
                book.id,
                book.title,
                book.author,
                book.isbn,
                book.total_copies,
                book.available_copies,

                book.created_at.isoformat(),
            ],
        )





        self._con.commit()

    def find_all(self) -> List[Book]:
        cursor = self._con.execute(
            """
            SELECT * FROM books
            """
        )
        return [
            Book(**row)
            for row in cursor.fetchall()
        ]

    def exists(self, book_id: str) -> bool:
        cursor = self._con.execute(
            """
            SELECT COUNT(*) FROM books WHERE id = ?
            """,
            [book_id],
        )
        count = cursor.fetchone()[0]
        return count > 0

    def find_by_id(self, book_id: str) -> Book:
        cursor = self._con.execute(
            """
            SELECT * FROM books WHERE id = ?
            """,
            [book_id],
        )
        row = cursor.fetchone()
        if not row:
            raise BookNotFoundError(f"Book with ID {book_id} not found")
        return Book(**row)