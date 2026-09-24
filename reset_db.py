import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from backend.app.db import Base, engine

# Import all models
from backend.app.auth.models import *
from backend.app.organizations.models import *
from backend.app.github.models import *
from backend.app.review.models import *
from backend.app.rag.models import *
from backend.app.chat.models import *
from backend.app.audit.models import *
from backend.app.webhooks.models import *

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
    
    print("Cleaning up duplicate indexes in metadata...")
    for table in Base.metadata.tables.values():
        unique_indexes = []
        seen_index_names = set()
        for idx in table.indexes:
            if idx.name not in seen_index_names:
                unique_indexes.append(idx)
                seen_index_names.add(idx.name)
        table.indexes = set(unique_indexes)

    print("Recreating all tables from models...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    reset_db()
