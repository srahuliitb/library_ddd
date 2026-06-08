"""
Borrowing HTTP routes.

Receives a pre-wired LoanService via the factory function. The service is
the only thing the routes know about - they don't even know the catalog
context exists. The catalog interaction is hidden inside LoanService.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from modules.borrowing.application.services.loan_service import LoanService
from modules.borrowing.domain.loan import LoanNotFoundError, LoanAlreadyReturnedError
from modules.catalog.domain.book import BookNotFoundError, BookUnavailableError
from modules.borrowing.interface.schemas import LoanCreateRequest, LoanResponse


def borrowing_router(service: LoanService) -> APIRouter:
    router = APIRouter(tags=["Borrowing"])

    @router.post(
        "/loans",
        response_model=LoanResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Borrow a book (interacts with Catalog context)",
    )
    def create_loan(payload: LoanCreateRequest) -> LoanResponse:
        try:
            loan = service.borrow_book(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except BookNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except BookUnavailableError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"Missing field: {exc}")
        return _to_response(loan)

    @router.post(
        "/loans/{loan_id}/return",
        response_model=LoanResponse,
        summary="Return a borrowed book (interacts with Catalog context)",
    )
    def return_loan(loan_id: str) -> LoanResponse:
        try:
            loan = service.return_book(loan_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except LoanNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except LoanAlreadyReturnedError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return _to_response(loan)

    @router.get(
        "/loans/{loan_id}",
        response_model=LoanResponse,
        summary="Get a loan by id",
    )
    def get_loan(loan_id: str) -> LoanResponse:
        try:
            loan = service.get_loan(loan_id)
        except LoanNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return _to_response(loan)

    @router.get(
        "/loans",
        response_model=list[LoanResponse],
        summary="List all loans",
    )
    def list_loans() -> list[LoanResponse]:
        loans = service.list_loans()
        return [_to_response(loan) for loan in loans]

    def _to_response(loan) -> LoanResponse:
        return LoanResponse(
            id=loan.id,
            book_id=loan.book_id,
            borrower_name=loan.borrower_name,
            borrowed_at=loan.borrowed_at,
            returned_at=loan.returned_at,
            is_active=loan.is_active(),
        )

    return router
