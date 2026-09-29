from backend.app.db import engine, SessionLocal
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from sqlalchemy import text, inspect

def check_db():
    with engine.connect() as conn:
        assert 'repomind_db' in str(engine.url)
        
        insp = inspect(engine)
        print('Alembic version table exists:', 'alembic_version' in insp.get_table_names())
        
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        print('Alembic revision:', rev)
        
        exts = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchall()
        print('Vector extension present:', len(exts) > 0)
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        print('Admin user ID 1 exists:', user is not None and user.email == 'harshita.baghel@example.com')
        
        org = db.query(Organization).filter(Organization.id == 1).first()
        print('Organization ID 1 exists:', org is not None)
        
        membership = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == 1, OrganizationMembership.organization_id == 1).first()
        print('Admin membership is org_admin:', membership is not None and membership.role == RoleEnum.ORG_ADMIN)
        
        roles = [e.value for e in RoleEnum]
        print('Active roles:', roles)
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
