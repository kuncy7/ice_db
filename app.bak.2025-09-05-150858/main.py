from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.routers import auth, organizations, users, ice_rinks, system, measurements

settings = get_settings()
app = FastAPI(
    title="Ice Rink Energy API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (optional)
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.ratelimit_default])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    def ratelimit_handler(request: Request, exc: RateLimitExceeded):
        return exc.get_response()
except Exception:
    pass

# Swagger Bearer auth button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="API for ice rinks energy monitoring",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Make it global so the Authorize button appears
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Routers
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(ice_rinks.router)
app.include_router(system.router)
app.include_router(measurements.router)
