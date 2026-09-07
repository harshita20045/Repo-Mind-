from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    LLM_PROVIDER: str = "local"
    DEMO: bool = False
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"

settings = Settings()
