"""Pydantic schemas - the HTTP-facing DTOs for the catalog context."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BookCreateRequest(BaseModel):
    id: str = Field(..., description="Unique book id, e.g. 'B001'")
    title: str
    author: str
    isbn: str = Field(..., min_length=10)
    total_copies: int = Field(..., ge=1)
    available_copies: Optional[int] = Field(
        default=None,
        description="Defaults to total_copies if omitted.",
    )


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    isbn: str
    total_copies: int
    available_copies: int
    created_at: datetime
