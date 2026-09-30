import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from backend.app.db import engine

def verify():
    with engine.connect() as conn:
        # Check alembic version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"alembic_version: {version}")
        
        # Check tables
        tables = [
            "user", "organization", "repository", "pull_request", 
            "review_run", "github_identity", "automation_action"
        ]
        print("\nTable row counts:")
        for table in tables:
            res = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
            count = res.scalar()
            print(f"  {table}: {count}")
            
        # Check vector extension
        res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        ext = res.scalar()
        print(f"\npgvector extension exists: {bool(ext)}")

if __name__ == "__main__":
    verify()
