"""
CLI utility to link or update a GitHub Personal Access Token (PAT) for a user.
Usage:
    python backend/scripts/link_github_pat.py <YOUR_GITHUB_TOKEN> [USER_EMAIL]
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db import SessionLocal
from backend.app.auth.models import User
from backend.app.github.client import GitHubClient
from backend.app.github.service import upsert_github_identity
from backend.app.organizations.models import Repository

def link_token(token: str, email: str = "harshita.baghel@example.com"):
    token = token.strip()
    if not token:
        print("Error: Token cannot be empty.")
        sys.exit(1)

    print("1. Validating token against GitHub API...")
    try:
        client = GitHubClient(token)
        user_info = client.get_authenticated_user()
    except Exception as e:
        print(f"Error validating token with GitHub: {e}")
        sys.exit(1)

    github_user_id = str(user_info["id"])
    github_login = user_info["login"]
    print(f"   -> Authenticated as GitHub user: {github_login} (id: {github_user_id})")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Fall back to first user
            user = db.query(User).order_by(User.id.asc()).first()
            if not user:
                print(f"Error: No user found in database.")
                sys.exit(1)

        print(f"2. Linking to RepoMind user {user.id} ({user.email})...")
        identity = upsert_github_identity(
            db=db,
            user_id=user.id,
            github_user_id=github_user_id,
            github_login=github_login,
            access_token=token,
            refresh_token=None,
            expires_in=None,
        )
        identity.connection_status = "CONNECTED"

        # Reset failed repositories to unindexed so worker starts indexing immediately
        repos = db.query(Repository).filter(Repository.index_status == "failed").all()
        for r in repos:
            r.index_status = "unindexed"
            print(f"   -> Reset repository {r.id} ({r.github_owner}/{r.github_name}) to 'unindexed'")

        db.commit()
        print("\nSUCCESS: GitHub token linked successfully!")
        print("Background worker and reconciliation will now operate normally.")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/link_github_pat.py <YOUR_GITHUB_TOKEN> [USER_EMAIL]")
        sys.exit(1)

    pat_arg = sys.argv[1]
    email_arg = sys.argv[2] if len(sys.argv) > 2 else "harshita.baghel@example.com"
    link_token(pat_arg, email_arg)

