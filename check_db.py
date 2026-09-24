import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.db import engine
from sqlalchemy import text

def check_db():
    with engine.connect() as conn:
        users = conn.execute(text('SELECT id, email FROM "user"')).fetchall()
        print('Users:', users)
        ids = conn.execute(text('SELECT id, user_id, github_login FROM github_identity')).fetchall()
        print('GitHub Identities:', ids)
        creds = conn.execute(text('SELECT id, github_identity_id FROM github_credential')).fetchall()
        print('GitHub Credentials:', creds)
        orgs = conn.execute(text('SELECT id, name FROM organization')).fetchall()
        print('Organizations:', orgs)
        members = conn.execute(text('SELECT user_id, organization_id, role FROM organization_membership')).fetchall()
        print('Memberships:', members)

if __name__ == "__main__":
    check_db()
