"""
Catalog application service - implements both internal use cases AND the
AbstractBookService contract exposed to other contexts.

Depends ONLY on the domain layer (Book entity and BookRepository abstraction).
Never imports infrastructure.
"""
from __future__ import annotations

from typing import List

from modules.catalog.domain.book import Book, BookNotFoundError, BookRepository
from modules.catalog.domain.book_service import AbstractBookService


class BookService(AbstractBookService):
    """Use-case orchestrator for the catalog context."""

    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo  # injected - we don't know what backs it

    # ---- Internal use cases (called by catalog's own routes) ----

    def add_book(self, raw_data: dict) -> Book:
        book = Book(
            id=raw_data["id"],
            title=raw_data["title"],
            author=raw_data["author"],
            isbn=raw_data["isbn"],
            total_copies=raw_data["total_copies"],
            available_copies=raw_data.get("available_copies", raw_data["total_copies"]),
        )
        book.standardize()
        book.validate()
        self._repo.save(book)
        return book

    def list_books(self) -> List[Book]:
        return self._repo.list_all()

    def get_book(self, book_id: str) -> Book:
        if not self._repo.exists(book_id):
            raise BookNotFoundError(f"Book {book_id!r} not found in catalog.")
        return self._repo.get(book_id)

    # ---- Cross-context API (called by borrowing context) ----

    def reserve_copy(self, book_id: str) -> None:
        book = self.get_book(book_id)
        book.reserve_one_copy()
        self._repo.save(book)

    def release_copy(self, book_id: str) -> None:
        book = self.get_book(book_id)
        book.return_one_copy()
        self._repo.save(book)