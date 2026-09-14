from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core settings loaded from .env
    POSTGRES_URL: str
    JWT_SECRET: str
    FERNET_KEY: str
    DEMO: bool = False
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    BOOTSTRAP_TOKEN: Optional[str] = "fkjerngiorneognrengioirw0rrrrrth348h3fin3gnw3480"

    # LLM provider — Phase 8
    # "local": development/null provider (raises NotImplementedError on real reviews)
    # "claude": Anthropic Claude API (requires ANTHROPIC_API_KEY)
    LLM_PROVIDER: str = "local"
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-haiku-20241022"


settings = Settings()
