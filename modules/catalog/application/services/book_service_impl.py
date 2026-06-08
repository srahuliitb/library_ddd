"""
Catalog application service - implements both internal use cases AND the
AbstractBookService contract exposed to other contexts.

Depends ONLY on the domain layer (Book entity and BookRepository abstraction).
Never imports infrastructure.
"""
from __future__ import annotations

from abc import ABC
from typing import List

from modules.catalog.domain.book import Book, BookNotFoundError, BookUnavailableError
from modules.catalog.domain.book_repository import BookRepository
from modules.catalog.domain.book_service import AbstractBookService


class BookService(AbstractBookService, ABC):
    """Use-case orchestrator for the catalog context."""

    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo  # injected - we don't know what backs it

    # ---- Internal use cases (called by catalog's own routes) ----

    def add_book(self, raw_data: dict) -> Book:
        # available_copies is computed from total_copies in Book.__post_init__
        # but we can override it if provided (before validate is called)
        book = Book(
            id=raw_data["id"],
            title=raw_data["title"],
            author=raw_data["author"],
            isbn=raw_data["isbn"],
            total_copies=raw_data["total_copies"],
        )
        # Override available_copies if explicitly provided
        if "available_copies" in raw_data and raw_data["available_copies"] is not None:
            book.available_copies = raw_data["available_copies"]
        book.standardize()
        book.validate()
        self._repo.save(book)
        return book

    def list_books(self) -> List[Book]:
        return self._repo.list_all()

    def get_book(self, book_id: str) -> Book:
        """Get a book by id. Raises BookNotFoundError if not found."""
        if not self._repo.exists(book_id):
            raise BookNotFoundError(book_id)
        return self._repo.get(book_id)

    # ---- Cross-context API (called by borrowing context) ----

    def reserve_copy(self, book_id: str) -> None:
        """
        Reserve one copy of a book for borrowing.

        Decrements the book's available_copies. Raises:
          - BookNotFoundError: if the book doesn't exist
          - BookUnavailableError: if no copies are available
        """
        book = self.get_book(book_id)
        book.reserve_one_copy()
        self._repo.save(book)

    def release_copy(self, book_id: str) -> None:
        """
        Release one copy of a book back to the library.

        Increments the book's available_copies. Raises:
          - BookNotFoundError: if the book doesn't exist
        """
        book = self.get_book(book_id)
        book.return_one_copy()
        self._repo.save(book)