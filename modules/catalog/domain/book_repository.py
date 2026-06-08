"""
Abstract repository contract for the Catalog bounded context.

This is the ONLY interface that the application layer uses to access book data.
Infrastructure (DuckDB, in-memory, etc.) must implement this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .book import Book


class BookRepository(ABC):
    """Abstract contract for persisting books."""

    @abstractmethod
    def save(self, book: Book) -> None:
        """Save or update a book."""
        ...

    @abstractmethod
    def get(self, book_id: str) -> Book:
        """Get a book by id. Raises BookNotFoundError if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[Book]:
        """List all books in the catalog."""
        ...

    @abstractmethod
    def exists(self, book_id: str) -> bool:
        """Check if a book exists by id."""
        ...