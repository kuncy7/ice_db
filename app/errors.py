from fastapi import HTTPException
from datetime import datetime
from typing import Optional, Dict, Any

def create_error_response(
    status_code: int,
    message: str,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create standardized error response"""
    error_data = {
        "code": code or f"HTTP_{status_code}",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if details:
        error_data["details"] = details
    
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "error": error_data
        }
    )

def http_400(detail: str, code: str = "BAD_REQUEST", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(400, detail, code, details)

def http_401(detail: str = "Unauthorized", code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(401, detail, code, details)

def http_403(detail: str = "Forbidden", code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(403, detail, code, details)

def http_404(detail: str = "Not Found", code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(404, detail, code, details)

def http_422(detail: str = "Validation Error", code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(422, detail, code, details)

def http_429(detail: str = "Too Many Requests", code: str = "RATE_LIMIT_EXCEEDED", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(429, detail, code, details)

def http_500(detail: str = "Internal Server Error", code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
    raise create_error_response(500, detail, code, details)
