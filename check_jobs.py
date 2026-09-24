import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.db import engine
from sqlalchemy import text

def check_jobs():
    with engine.connect() as conn:
        repos = conn.execute(text("SELECT id, index_status FROM repository")).fetchall()
        print("Repositories:", repos)
        runs = conn.execute(text("SELECT id, status FROM review_run")).fetchall()
        print("Review runs:", runs)

if __name__ == "__main__":
    check_jobs()
