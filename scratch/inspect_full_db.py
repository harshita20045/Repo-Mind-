import os
import sys
from sqlalchemy import text, inspect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.db import engine, SessionLocal

inspector = inspect(engine)
tables = inspector.get_table_names()
db = SessionLocal()

print("=== DATABASE TABLE ROW COUNTS ===")
non_zero = []
zeros = []

for t in sorted(tables):
    try:
        cnt = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
        if cnt > 0:
            non_zero.append((t, cnt))
        else:
            zeros.append(t)
    except Exception as e:
        db.rollback()
        print(f"Error reading {t}: {e}")

print("\n--- TABLES WITH DATA ---")
for t, cnt in non_zero:
    print(f"  {t}: {cnt}")

print("\n--- EMPTY TABLES ---")
for t in zeros:
    print(f"  {t}: 0")

print("\n=== REPOSITORIES ===")
try:
    repos = db.execute(text('SELECT id, name, full_name, owner, is_active FROM repository')).fetchall()
    for r in repos:
        print(f"  ID: {r[0]}, Name: {r[1]}, Full: {r[2]}, Owner: {r[3]}, Active: {r[4]}")
except Exception as e:
    print(f"  Error querying repository: {e}")

print("\n=== USERS ===")
try:
    users = db.execute(text('SELECT id, email, username, role, is_active FROM "user"')).fetchall()
    for u in users:
        print(f"  ID: {u[0]}, Email: {u[1]}, Username: {u[2]}, Role: {u[3]}, Active: {u[4]}")
except Exception as e:
    print(f"  Error querying user: {e}")

print("\n=== ORGANIZATIONS ===")
try:
    orgs = db.execute(text('SELECT id, name, slug FROM organization')).fetchall()
    for o in orgs:
        print(f"  ID: {o[0]}, Name: {o[1]}, Slug: {o[2]}")
except Exception as e:
    print(f"  Error querying organization: {e}")

print("\n=== PULL REQUESTS ===")
try:
    prs = db.execute(text('SELECT id, repository_id, pr_number, title, state, author FROM pull_request')).fetchall()
    for p in prs:
        print(f"  ID: {p[0]}, RepoID: {p[1]}, PR#: {p[2]}, Title: {p[3]}, State: {p[4]}, Author: {p[5]}")
except Exception as e:
    print(f"  Error querying pull_request: {e}")

print("\n=== REPOSITORY BLUEPRINTS ===")
try:
    bps = db.execute(text('SELECT id, repository_id, status, architecture_pattern, summary FROM repository_blueprint')).fetchall()
    for b in bps:
        print(f"  ID: {b[0]}, RepoID: {b[1]}, Status: {b[2]}, Pattern: {b[3]}, Summary: {str(b[4])[:60]}...")
except Exception as e:
    print(f"  Error querying repository_blueprint: {e}")

db.close()
