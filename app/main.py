# --- Sekcja 1: Importy ---
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Opcjonalne importy dla Rate Limiting
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_ENABLED = True
except ImportError:
    SLOWAPI_ENABLED = False

# Importy z Twojego projektu
from app.config import get_settings
from app.routers import (auth, organizations, users, ice_rinks, system, 
                           measurements, service_tickets, weather)
from app.tasks import fetch_weather_forecasts_task


# --- Sekcja 2: Definicja cyklu życia aplikacji (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza zadaniami uruchamianymi przy starcie i zamykaniu aplikacji.
    """
    print("Application startup... starting background tasks.")
    task = asyncio.create_task(fetch_weather_forecasts_task())
    yield
    print("Application shutdown... cleaning up.")
    task.cancel()


# --- Sekcja 3: Główna instancja aplikacji FastAPI ---
settings = get_settings()
app = FastAPI(
    title="Ice Rink Energy API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
    lifespan=lifespan
)


# --- Sekcja 4: Konfiguracja Middleware (CORS, Rate Limiting) ---
origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if SLOWAPI_ENABLED:
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.ratelimit_default])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    def ratelimit_handler(request: Request, exc: RateLimitExceeded):
        return exc.get_response()


# --- Sekcja 5: Modyfikacja schematu OpenAPI (Swagger) ---
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
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# --- Sekcja 6: Rejestracja Routerów ---
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(ice_rinks.router)
app.include_router(system.router)
app.include_router(measurements.router)
app.include_router(service_tickets.router)
app.include_router(weather.router)
