from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic v2 config: wczytaj .env i ignoruj nieznane zmienne (app_env, app_host itp.)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://ice:iceuser@127.0.0.1:5432/ice_db"
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 60
    refresh_token_expires_days: int = 30
    cors_origins: str = "*"

    # Rate limiting (Etap 1)
    ratelimit_default: str = "1000/hour"
    ratelimit_ssp: str = "100/minute"
    ratelimit_weather: str = "60/minute"
