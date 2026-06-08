"""
Abstract service interface for the Catalog bounded context.

This is the ONLY contract that other bounded contexts can depend on.
It is defined in the domain layer and implemented in the application layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .book import Book, BookNotFoundError, BookUnavailableError


class AbstractBookService(ABC):
    """
    Abstract service defining the public contract of the Catalog context.

    Other bounded contexts (like Borrowing) depend ONLY on this interface,
    never on concrete implementations or infrastructure details.
    """

    @abstractmethod
    def get_book(self, book_id: str) -> Book:
        """Get a book by id. Raises BookNotFoundError if not found."""
        ...

    @abstractmethod
    def reserve_copy(self, book_id: str) -> None:
        """
        Reserve one copy of a book for borrowing.

        Decrements the book's available_copies. Raises:
          - BookNotFoundError: if the book doesn't exist
          - BookUnavailableError: if no copies are available
        """
        ...

    @abstractmethod
    def release_copy(self, book_id: str) -> None:
        """
        Release one copy of a book back to the library.

        Increments the book's available_copies. Raises:
          - BookNotFoundError: if the book doesn't exist
        """
        ...