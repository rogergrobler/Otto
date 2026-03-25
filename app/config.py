from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://otto:otto@localhost:5432/otto"

    # LLM
    LLM_PROVIDER: str = "claude"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-20250514"
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

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    CONVERSATION_TIMEOUT_HOURS: int = 4
    MEMORY_SUMMARY_MAX_TOKENS: int = 2000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
