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
        # NOTA (bug corrigido): "professor@avalia.local" NUNCA funciona como e-mail de
        # login porque o schema LoginRequest usa pydantic.EmailStr, cuja biblioteca
        # email_validator rejeita domínios "special-use" da IANA (local/test/invalid/
        # onion/arpa/localhost) por não serem globalmente roteáveis (RFC 6762). Toda
        # tentativa de login com domínio .local retorna HTTP 422 antes de consultar o
        # banco. Usar sempre um domínio válido (ex.: .example, RFC 2606) para a conta demo.
        self.seed_professor_email = os.getenv("SEED_PROFESSOR_EMAIL", "professor.demo@avalia-platform.example")
        self.seed_professor_password = os.getenv("SEED_PROFESSOR_PASSWORD", "DemoAvalIA123!")


@lru_cache
def get_settings() -> Settings:
    return Settings()
