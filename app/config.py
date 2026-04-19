import json

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Always allowed regardless of env var
_ALWAYS_ALLOWED_ORIGINS = [
    "https://frontend-lyart-ten-72.vercel.app",
    "http://localhost:3000",
]


class Settings(BaseSettings):
    # Database — Railway provides postgresql://, we need postgresql+asyncpg://
    DATABASE_URL: str = "postgresql+asyncpg://otto:otto@localhost:5432/otto"

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # LLM
    LLM_PROVIDER: str = "claude"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "claude-haiku-4-5-20251001"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Auth
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Wearable integrations
    WHOOP_CLIENT_ID: str = ""
    WHOOP_CLIENT_SECRET: str = ""

    # CORS — comma-separated or JSON list of allowed origins
    CORS_ORIGINS: list[str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                parsed: list[str] = json.loads(v)
            else:
                parsed = [o.strip() for o in v.split(",") if o.strip()]
        elif isinstance(v, list):
            parsed = v
        else:
            parsed = []
        # Merge with always-allowed origins (deduplicated)
        merged = list(dict.fromkeys(_ALWAYS_ALLOWED_ORIGINS + parsed))
        return merged

    # Storage (local filesystem for Phase 1; swap for S3 later)
    UPLOAD_DIR: str = "uploads"

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    CONVERSATION_TIMEOUT_HOURS: int = 4
    MEMORY_SUMMARY_MAX_TOKENS: int = 2000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
