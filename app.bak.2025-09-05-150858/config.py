from pydantic import BaseModel
from functools import lru_cache
import os
from pathlib import Path

# Optional: load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    ENV_PATH = os.getenv("ENV_FILE") or str(PROJECT_ROOT / ".env")
    load_dotenv(ENV_PATH, override=True)
except Exception:
    pass

class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://ice:iceuser@127.0.0.1:5432/ice_db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expires_min: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    refresh_expires_days: int = int(os.getenv("REFRESH_EXPIRES_DAYS", "30"))
    ratelimit_default: str = os.getenv("RATELIMIT_DEFAULT", "1000/hour")
    ratelimit_ssp: str = os.getenv("RATELIMIT_SSP", "100/minute")
    ratelimit_weather: str = os.getenv("RATELIMIT_WEATHER", "60/minute")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

@lru_cache
def get_settings() -> Settings:
    return Settings()
