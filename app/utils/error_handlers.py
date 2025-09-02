from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.responses import error_envelope


def register_error_handlers(app):
    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        # np. duplikaty, naruszenia constraintów
        return JSONResponse(
            status_code=409,
            content=error_envelope(409, "Conflict", None),
        )

    @app.exception_handler(ValidationError)
    async def handle_validation_error(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content=error_envelope(422, "Validation error", exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        # Zwracamy oryginalny status (401/403/404/...), ale w naszej kopercie
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.status_code, exc.detail, None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Ostatnia linia obrony
        return JSONResponse(
            status_code=500,
            content=error_envelope(500, "Internal server error", None),
        )
