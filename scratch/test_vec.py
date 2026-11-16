import sys
sys.path.insert(0, ".")
from backend.app.core.config import settings
from sqlalchemy import create_engine, text

eng = create_engine(settings.POSTGRES_URL)
with eng.connect() as conn:
    val = conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).scalar()
    print("Has vector extension in PG available extensions:", bool(val))
