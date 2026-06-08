"""
Borrowing HTTP routes.

Receives a pre-wired LoanService via the factory function. The service is
the only thing the routes know about - they don't even know the catalog
context exists. The catalog interaction is hidden inside LoanService.
"""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from modules.borrowing.application.services.loan_service import LoanService
from modules.borrowing.domain.loan import Loan
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
            # Catch any validation errors from the service
            raise HTTPException(status_code=400, detail=str(exc))
        except KeyError as exc:
            # Catch missing required fields
            raise HTTPException(status_code=400, detail=f"Missing field: {exc}")
        except Exception as exc:
            # Any other errors (e.g., book not found, no copies)
            raise HTTPException(status_code=409, detail=str(exc))
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
            # Catch validation errors
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            # Loan not found or already returned
            raise HTTPException(status_code=404 if "not found" in str(exc).lower() else 409, detail=str(exc))
        return _to_response(loan)

    @router.get("/loans/{loan_id}")
    def get_loan(loan_id: str) -> LoanResponse | None:
        try:
            return _to_response(service.get_loan(loan_id))
        except ValueError as exc:
            return None
        except Exception as exc:
            return None

    def _to_response(loan: dict) -> LoanResponse:
        return LoanResponse(
            id=loan["id"],
            book_id=loan["book_id"],
            borrower_name=loan["borrower_name"],
            borrowed_at=loan["borrowed_at"],
            returned_at=loan["returned_at"],
            status=loan["status"],
        )
