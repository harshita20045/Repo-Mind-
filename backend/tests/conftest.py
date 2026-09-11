import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import get_db, Base
from backend.app.core.config import settings

# For schema creation, ensure all models are known to Base.metadata
from backend.app.auth.models import User, Organization, OrganizationMembership
from backend.app.organizations.models import Project, Repository, GithubConnection
from backend.app.github.models import PullRequest, Commit

# Explicitly configure the test database URL
from sqlalchemy.engine.url import make_url
original_url = make_url(settings.POSTGRES_URL)
TEST_POSTGRES_URL = original_url.set(database="repomind_test").render_as_string(hide_password=False)

# Prevent falling back to development configuration
if TEST_POSTGRES_URL == settings.POSTGRES_URL:
    pytest.exit("CRITICAL: Test database URL exactly matches development database URL. Aborting.")

# Create dedicated test engine
engine = create_engine(TEST_POSTGRES_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _verify_test_db_identity():
    """Runtime safety check that queries the live connection identity."""
    try:
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            if db_name != "repomind_test":
                pytest.exit(f"CRITICAL SAFETY GUARD FAILED: Connected database is '{db_name}', expected 'repomind_test'.")
    except Exception as e:
        pytest.exit(f"CRITICAL: Failed to verify database identity. Error: {str(e)}")

# Perform identity verification before anything else
_verify_test_db_identity()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in the test database once per session."""
    _verify_test_db_identity()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db_session():
    """Provides a fresh database session, clearing all tables beforehand."""
    _verify_test_db_identity()
    
    session = TestingSessionLocal()
    try:
        # Clear all tables dynamically safely
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    """Provides a TestClient with the dependency overridden to use the test DB."""
    # Override settings directly since it's already instantiated
    settings.BOOTSTRAP_TOKEN = "test_bootstrap_token"
    os.environ["BOOTSTRAP_TOKEN"] = "test_bootstrap_token"
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
