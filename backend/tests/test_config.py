from backend.app.core.config import settings

def test_settings_loaded():
    assert settings.POSTGRES_URL is not None
    assert settings.JWT_SECRET is not None
    assert settings.FERNET_KEY is not None

def test_embedding_model_specification():
    assert settings.EMBEDDING_MODEL == "sentence-transformers/all-mpnet-base-v2"
