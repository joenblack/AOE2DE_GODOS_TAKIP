from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AoE2:DE Stats Tracker"
    DEBUG: bool = True
    
    # Database
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_DB: str = "aoe2stats"
    DATABASE_HOST: str = "localhost" # 'db' inside docker
    DATABASE_PORT: int = 5432
    
    # If set in env (e.g. for SQLite local dev), this takes precedence.
    # Otherwise we could construct it, but Pydantic defaults are static.
    # Let's provide a default that is the postgres one, or just allow it to be overwritten.
    DATABASE_URL: str = "postgresql://admin:admin@localhost:5432/aoe2stats"

    # External APIs

    # External APIs
    AOESTATS_DUMP_URL: str = "https://aoestats.io/api/db_dumps"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
