import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from backend.app.db import engine

def check_tables():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in res]
        print("Tables in public schema:")
        for t in tables:
            print(f" - {t}")
            
if __name__ == "__main__":
    check_tables()
