import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Importy z Twojego projektu
from app.config import get_settings
from app.routers import (auth, organizations, users, ice_rinks, system,
                           measurements, service_tickets, weather)
from app.tasks import fetch_weather_forecasts_task

def create_app() -> FastAPI:
    # --- Definicja cyklu życia aplikacji (Lifespan) ---
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("Application startup... starting background tasks.")
        task = asyncio.create_task(fetch_weather_forecasts_task())
        yield
        print("Application shutdown... cleaning up.")
        task.cancel()

    # --- Główna instancja aplikacji FastAPI ---
    settings = get_settings()
    app = FastAPI(
        title="Ice Rink Energy API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )

    # --- Konfiguracja Middleware (np. CORS) ---
    origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rejestracja Routerów ---
    app.include_router(auth.router)
    app.include_router(organizations.router)
    app.include_router(users.router)
    app.include_router(ice_rinks.router)
    app.include_router(system.router)
    app.include_router(measurements.router)
    app.include_router(service_tickets.router)
    app.include_router(weather.router)

    # --- DODANA SEKCJA - Konfiguracja Swaggera dla autoryzacji JWT ---
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
        # Aplikuj schemat `bearerAuth` globalnie na wszystkie endpointy
        openapi_schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    # --- KONIEC DODANEJ SEKCJI ---
    
    return app

# Tworzymy instancję aplikacji na potrzeby Uvicorn
app = create_app()
