from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from datetime import datetime, timezone
from app.utils.responses import success_envelope, error_envelope
from fastapi import FastAPI, Request, HTTPException, Depends
from app.database import engine, Base
from app.utils.error_handlers import register_error_handlers
from app.endpoints import organizations, users, auth, ice_rinks, measurements

# Zakomentowane, ponieważ baza jest zarządzana przez skrypt SQL
# Base.metadata.create_all(bind=engine)


def success_envelope(data):
    return {"success": True, "data": data}

def error_envelope(message:str, code:int, details=None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
app = FastAPI(
    title="Centralny System Zarządzania Energią dla Lodowisk",
    description="API do zarządzania danymi z lodowisk.",
    version="1.0.0 (dev)"
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(ice_rinks.router, prefix="/api/ice-rinks", tags=["Ice Rinks"])
app.include_router(measurements.router, prefix="/api/ice-rinks", tags=["Measurements"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Witaj w API Systemu Zarządzania Energią dla Lodowisk!"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=error_envelope(exc.detail, exc.status_code))

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=error_envelope("Validation error", HTTP_422_UNPROCESSABLE_ENTITY, details=exc.errors()))

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error_envelope("Internal server error", 500))
