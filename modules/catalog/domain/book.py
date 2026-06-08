"""
Domain entities for the Catalog bounded context.

This file has ZERO imports from any other layer. It is the stable core:
everything else in the system depends on it, it depends on nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


class BookNotFoundError(Exception):
    """Raised when a book id does not exist in the catalog."""


class BookUnavailableError(Exception):
    """Raised when trying to mark a book as borrowed but no copies are free."""


@dataclass
class Book:
    """A book in the library catalog - the core aggregate."""

    id: str
    title: str
    author: str
    isbn: str
    total_copies: int
    available_copies: int = field(init=False)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not hasattr(self, "available_copies") or self.available_copies is None:
            self.available_copies = self.total_copies
        self.validate()

    # ---- Business rules (the 'Domain' part of DDD) ----

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Book id is required.")
        if not self.title or not self.title.strip():
            raise ValueError("Book title is required.")
        if not self.author or not self.author.strip():
            raise ValueError("Book author is required.")
        if not self.isbn or len(self.isbn) < 10:
            raise ValueError("Book ISBN must be at least 10 characters.")
        if self.total_copies < 1:
            raise ValueError("Book must have at least one copy.")
        if self.available_copies < 0:
            raise ValueError("available_copies cannot be negative.")
        if self.available_copies > self.total_copies:
            raise ValueError("available_copies cannot exceed total_copies.")

    def standardize(self) -> None:
        """Normalize book data before saving."""
        self.id = self.id.strip()
        self.title = self.title.strip()
        self.author = self.author.strip()

    def reserve_one_copy(self) -> None:
        """Decrement available copies when a loan is created."""
        if self.available_copies < 1:
            raise BookUnavailableError(
                f"Cannot reserve book {self.id!r}: no copies available."
            )
        self.available_copies -= 1

    def return_one_copy(self) -> None:
        """Increment available copies when a loan is returned."""
        if self.available_copies >= self.total_copies:
            raise ValueError(
                f"Cannot return book {self.id!r}: all copies already in library."
            )
        self.available_copies += 1

