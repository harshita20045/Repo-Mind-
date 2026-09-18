from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional


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
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    # When omitted, secure cookies are enabled automatically outside local
    # development/test environments. Set explicitly only for an intentional
    # deployment override (for example, local HTTPS development).
    COOKIE_SECURE: Optional[bool] = None
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    BOOTSTRAP_TOKEN: Optional[str] = "fkjerngiorneognrengioirw0rrrrrth348h3fin3gnw3480"

    # LLM provider — Phase 8
    # "local": development/null provider (raises NotImplementedError on real reviews)
    # "gemini": Google Gemini API (requires GEMINI_API_KEY)
    # "groq": Groq API (requires GROQ_API_KEY)
    LLM_PROVIDER: str = "local"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # GitHub Webhook — RepoMind 2.0
    # Set this to the secret configured in GitHub repo webhook settings.
    # If not set, all incoming webhooks will be rejected with 401.
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # Context bounding limits
    RAG_MAX_CHUNKS: int = 5
    MAX_DIFF_CHARS: int = 30000
    MAX_LINTER_CHARS: int = 5000

    @property
    def session_cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.ENVIRONMENT not in {"development", "test"}

settings = Settings()
