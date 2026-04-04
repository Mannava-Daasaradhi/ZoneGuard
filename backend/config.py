from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://zoneguard:zoneguard_dev@localhost:5432/zoneguard"
    redis_url: str = "redis://localhost:6379/0"
    openweathermap_api_key: str = ""
    gemini_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
