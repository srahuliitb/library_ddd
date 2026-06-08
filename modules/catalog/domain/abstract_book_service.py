"""
Abstract service interface exposed to OTHER bounded contexts.

This is the public API of the catalog context. The borrowing context can
only talk to the catalog through this interface - it never imports the
concrete BookService. This keeps the contexts decoupled: we could replace
DuckDB with something else and borrowing would not notice.
"""
from __future__ import annotations

from typing import Protocol

from modules.catalog.domain.book import Book


class AbstractBookService(Protocol):
    """What the rest of the world is allowed to ask the catalog context."""

    def get_book(self, book_id: str) -> Book: ...
    def reserve_copy(self, book_id: str) -> None: ...
    def release_copy(self, book_id: str) -> None: ...
