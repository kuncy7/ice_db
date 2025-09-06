from fastapi import HTTPException

def http_400(detail: str):
    raise HTTPException(status_code=400, detail=detail)

def http_401(detail: str = "Unauthorized"):
    raise HTTPException(status_code=401, detail=detail)

def http_403(detail: str = "Forbidden"):
    raise HTTPException(status_code=403, detail=detail)

def http_404(detail: str = "Not Found"):
    raise HTTPException(status_code=404, detail=detail)
