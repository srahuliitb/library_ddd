We need to apply suggested edit to original code. The original code defines LoanNotFoundError, LoanError, LoanStatus, Loan etc. The suggested edit replaces a bunch with a different version: includes new imports, cross-context dependency import, new exception classes, new Loan dataclass (different fields), new methods, and defines LoanRepository Protocol and __all__ etc.

We need to apply suggested edit to original code. Means we replace original content with edited version. However we must preserve any comments unless changes require modifying them. The suggested edit includes a docstring at top, imports, etc. Likely we replace whole file.

Thus final code should be the suggested edit content (modified file). It includes docstring, imports, classes. The __all__ list ends partially; need to include closing brackets etc. The suggested edit ends with __all__ = [ "Loan", but missing rest? Possibly truncated. We need to infer the full __all__ contents. The original __all__ was ["Loan", "LoanNotFoundError", "LoanError", "LoanStatus"]. In new version, __all__ likely includes "Loan", "LoanNotFoundError", "NoAvailableCopiesError", "LoanAlreadyReturnedError", "LoanRepository". But suggestion shows only "Loan". Might be incomplete.

But we should follow suggestion: apply only modifications indicated. It ends abruptly; maybe we just keep as is. But code must be syntactically correct. The __all__ list cannot be incomplete. The suggestion ends with a comma after "Loan", and then no closing bracket. Might be a formatting oversight. To make file valid, we need to close the list. Probably we should include "Loan", "LoanNotFoundError", "NoAvailableCopiesError", "LoanAlreadyReturnedError", "LoanRepository". Or at least close after "Loan". Since we must output complete modified file, we need to ensure syntactically valid.

I'll include __all__ = ["Loan", "LoanNotFoundError", "NoAvailableCopiesError", "LoanAlreadyReturnedError", "LoanRepository"].

Also the imports: from modules.catalog.domain.book_service import AbstractBookService is referenced but not used; we keep as is.

Remove original definitions. So final code:

docstring, imports, classes, __all__.

Let's construct final code accordingly.
"""
Borrowing domain entities and abstract repository.

Imports ONLY from the catalog domain's ABSTRACT service interface
(AbstractBookService) - never the concrete service or any infrastructure.
This is how the two contexts stay decoupled: borrowing talks to "a catalog"
through a contract, not to a specific implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Protocol

# Cross-context dependency: import the abstract interface only.
from modules.catalog.domain.book_service import AbstractBookService


class LoanNotFoundError(Exception):
    """Raised when a loan id does not exist."""


class NoAvailableCopiesError(Exception):
    """Raised when borrowing a book that has no free copies."""


class LoanAlreadyReturnedError(Exception):
    """Raised when trying to return an already-returned loan."""


@dataclass
class Loan:
    """A loan aggregate - one borrower taking one book."""

    id: str
    book_id: str
    borrower_name: str
    borrowed_at: datetime = field(default_factory=datetime.utcnow)
    returned_at: datetime | None = None
    def is_active(self) -> bool:
        return self.returned_at is None
    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Loan id is required.")
        if not self.book_id or not self.book_id.strip():
            raise ValueError("book_id is required.")
        if not self.borrower_name or not self.borrower_name.strip():
            raise ValueError("borrower_name is required.")

    def standardize(self) -> None:
        self.borrower_name = self.borrower_name.strip()
    def mark_returned(self) -> None:
        if not self.is_active():
            raise LoanAlreadyReturnedError(
                f"Loan {self.id!r} was already returned at {self.returned_at}."
            )
        self.returned_at = datetime.utcnow()


class LoanRepository(Protocol):
    """Abstract repository for Loan aggregates."""

    def save(self, loan: Loan) -> None: ...
    def get(self, loan_id: str) -> Loan: ...
    def list_all(self) -> List[Loan]: ...


# Re-export the cross-context types so application code can import them
# from a single, semantically meaningful place.
__all__ = [
    "Loan",
    "LoanNotFoundError",
    "NoAvailableCopiesError",
    "LoanAlreadyReturnedError",
    "LoanRepository",
]

