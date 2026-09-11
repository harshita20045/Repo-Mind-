import os
from dotenv import load_dotenv
load_dotenv(".env")
print("POSTGRES_URL from .env:", os.environ.get("POSTGRES_URL"))

from backend.app.db import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    print("--- Postgres configuration ---")
    print("Version:", db.execute(text("SELECT version();")).scalar())
    print("Current Database:", db.execute(text("SELECT current_database();")).scalar())
    
    settings = db.execute(text("SELECT name, setting FROM pg_settings WHERE name IN ('data_directory', 'config_file', 'port');")).fetchall()
    for row in settings:
        print(f"{row[0]}: {row[1]}")
        
    print("--- pgvector check ---")
    pg_available = db.execute(text("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'vector';")).fetchall()
    print("pg_available_extensions:", pg_available)
    pg_ext = db.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchall()
    print("pg_extension:", pg_ext)
finally:
    db.close()
