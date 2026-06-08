"""Pydantic schemas - HTTP DTOs for the borrowing context."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoanCreateRequest(BaseModel):
    id: str = Field(..., description="Unique loan id, e.g. 'L001'")
    book_id: str = Field(..., description="Id of the book in the catalog.")
    borrower_name: str


class LoanResponse(BaseModel):
    id: str
    book_id: str
    borrower_name: str
    borrowed_at: datetime
    returned_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True
