import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import create_engine, text
from backend.app.core.config import settings
from sqlalchemy.engine.url import make_url

original_url = make_url(settings.POSTGRES_URL)
TEST_POSTGRES_URL = original_url.set(database="repomind_test").render_as_string(hide_password=False)
engine = create_engine(TEST_POSTGRES_URL)

try:
    with engine.connect() as conn:
        print("--- alembic_version ---")
        res = conn.execute(text("SELECT * FROM alembic_version"))
        for row in res:
            print(row)
except Exception as e:
    print("alembic_version error:", e)

try:
    with engine.connect() as conn:
        print("--- review_run columns ---")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='review_run'"))
        for row in res:
            print(row[0])
except Exception as e:
    print("review_run error:", e)
