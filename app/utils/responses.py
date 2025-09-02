from datetime import datetime, timezone

def success_envelope(data):
    return {"success": True, "data": data}

def error_envelope(message: str, code: int, details=None):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
