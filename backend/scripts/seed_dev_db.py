import sys
import os
import logging

# Add the root 'backend' dir so 'app' can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.db import SessionLocal, Base, engine
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.auth.service import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_safe_environment():
    logger.info("Verifying environment safety...")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
    logger.info(f"Database URL: {settings.POSTGRES_URL}")

    # Ensure it's not production
    if getattr(settings, 'ENVIRONMENT', 'development') != 'development':
        raise Exception("ABORT: ENVIRONMENT is not 'development'.")
    
    # Ensure it looks like a local postgres
    if "localhost" not in settings.POSTGRES_URL and "127.0.0.1" not in settings.POSTGRES_URL:
        raise Exception("ABORT: POSTGRES_URL does not point to localhost. This might not be a local dev DB.")
    
    logger.info("Safety check passed. Proceeding with Database Reset.")

def reset_database(db: Session):
    logger.info("Resetting application data (Truncating tables)...")
    
    # We truncate tables instead of drop/create to preserve schema & alembic state.
    # A single TRUNCATE statement across all data tables.
    tables = [
        "chat_message", "chat_session", 
        "chunk", "document",
        "review_evidence", "review", "pull_request", 
        "repository", "project", 
        "organization_membership", "organization", 
        "user"
    ]
    
    # Let's dynamically find all tables just to be safe, filtering out alembic_version
    try:
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        actual_tables = [row[0] for row in result.fetchall() if row[0] != "alembic_version"]
        
        if actual_tables:
            logger.info(f"Truncating tables: {actual_tables}")
            tables_csv = ", ".join([f'"{t}"' for t in actual_tables])
            db.execute(text(f"TRUNCATE TABLE {tables_csv} CASCADE;"))
            db.commit()
            logger.info("Tables truncated successfully (alembic_version preserved).")
        else:
            logger.info("No tables to truncate.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset DB: {e}")
        raise

def seed_database(db: Session):
    logger.info("Seeding deterministic data...")
    
    # 1. Create Users
    admin_email = "admin@example.com"
    admin_password = "Password123!"
    lead_email = "lead@example.com"
    lead_password = "Password123!"
    dev_email = "developer@example.com"
    dev_password = "Password123!"

    admin_user = User(email=admin_email, password_hash=hash_password(admin_password))
    lead_user = User(email=lead_email, password_hash=hash_password(lead_password))
    dev_user = User(email=dev_email, password_hash=hash_password(dev_password))
    
    db.add_all([admin_user, lead_user, dev_user])
    db.commit()
    
    # 2. Create Organization
    org = Organization(name="RepoMind Development")
    db.add(org)
    db.commit()
    
    # 3. Memberships
    m_admin = OrganizationMembership(user_id=admin_user.id, organization_id=org.id, role=RoleEnum.ORG_ADMIN)
    m_lead = OrganizationMembership(user_id=lead_user.id, organization_id=org.id, role=RoleEnum.TEAM_LEAD)
    m_dev = OrganizationMembership(user_id=dev_user.id, organization_id=org.id, role=RoleEnum.DEVELOPER)
    
    db.add_all([m_admin, m_lead, m_dev])
    db.commit()

    # 4. Create Projects
    p_payments = Project(name="Payments Platform", organization_id=org.id)
    p_dev = Project(name="Developer Tools", organization_id=org.id)
    
    db.add_all([p_payments, p_dev])
    db.commit()
    
    # 5. Create Repositories
    repo_a = Repository(
        project_id=p_payments.id,
        github_owner="local-dev",
        github_name="payments-service",
        default_branch="main",
        index_status="unindexed"
    )
    repo_b = Repository(
        project_id=p_dev.id,
        github_owner="local-dev",
        github_name="developer-platform",
        default_branch="main",
        index_status="unindexed"
    )
    
    db.add_all([repo_a, repo_b])
    db.commit()

    logger.info("Seeding complete.")
    logger.info("\n--- DEVELOPMENT USERS ---")
    logger.info(f"{admin_email} | Role: org_admin | Password: {admin_password}")
    logger.info(f"{lead_email} | Role: team_lead | Password: {lead_password}")
    logger.info(f"{dev_email} | Role: developer | Password: {dev_password}")
    logger.info("-------------------------")

if __name__ == "__main__":
    try:
        verify_safe_environment()
        db = SessionLocal()
        try:
            reset_database(db)
            seed_database(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Seed script failed: {e}")
