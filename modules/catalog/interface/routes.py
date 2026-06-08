"""
Catalog HTTP routes.

Receives a pre-wired BookService via the factory function. Never instantiates
anything itself - that is composition_root's job.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from modules.catalog.application.services.book_service import BookService
from modules.catalog.domain.book import (
    BookNotFoundError,
    BookUnavailableError,
)
from modules.catalog.interface.schemas import BookCreateRequest, BookResponse


def catalog_router(service: BookService) -> APIRouter:
    router = APIRouter(tags=["Catalog"])

    @router.post(
        "/books",
        response_model=BookResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Add a book to the catalog",
    )
    def create_book(payload: BookCreateRequest) -> BookResponse:
        try:
            book = service.add_book(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return BookResponse(**book.__dict__)

    @router.get(
        "/books",
        response_model=list[BookResponse],
        summary="List all books in the catalog",
    )
    def list_books() -> list[BookResponse]:
        books = service.list_books()
        return [BookResponse(**b.__dict__) for b in books]

    @router.get(
        "/books/{book_id}",
        response_model=BookResponse,
        summary="Get a single book by id",
    )
    def get_book(book_id: str) -> BookResponse:
        try:
            book = service.get_book(book_id)
        except BookNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return BookResponse(**book.__dict__)

    return router
