import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.db import engine
from sqlalchemy import text

def reset_jobs():
    with engine.begin() as conn:
        conn.execute(text("UPDATE repository SET index_status = 'pending'"))
        conn.execute(text("UPDATE review_run SET status = 'pending'"))
        print("Reset successful")

if __name__ == "__main__":
    reset_jobs()
