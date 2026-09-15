from backend.app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'vector'")).fetchall()
    print(result)
finally:
    db.close()
