from __future__ import annotations
import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.env = os.getenv("ENV", "development")
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://localhost:5432/avalia_dev"
        )
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-nao-use-em-producao")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_minutes = int(os.getenv("JWT_ACCESS_MINUTES", "30"))
        self.jwt_refresh_minutes = int(os.getenv("JWT_REFRESH_MINUTES", "1440"))
        self.ai_engine_url = os.getenv("AI_ENGINE_URL", "http://localhost:8001")
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        self.seed_professor_email = os.getenv("SEED_PROFESSOR_EMAIL", "professor@avalia.local")
        self.seed_professor_password = os.getenv("SEED_PROFESSOR_PASSWORD", "DemoAvalIA123!")


@lru_cache
def get_settings() -> Settings:
    return Settings()
