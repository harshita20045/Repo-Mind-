import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from backend.app.db import engine

def reset_db():
    print("Dropping schema public cascade...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            # Must recreate the vector extension because CASCADE dropped it
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception as e:
        print(f"Schema drop error (might be okay if empty): {e}")
    
    print("Running alembic upgrade head to recreate schema...")
    try:
        subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=True)
        print("Alembic upgrade completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Alembic upgrade failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_db()

