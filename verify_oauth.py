import sys
import os

sys.path.append(os.path.abspath('.'))

from backend.app.db import SessionLocal
from backend.app.auth.models import User, OrganizationMembership, RoleEnum
from backend.app.github.models import GitHubIdentity, GitHubCredential
from backend.app.organizations.models import Repository, Project

def verify():
    db = SessionLocal()
    
    user = db.query(User).filter(User.email == "harshita.baghel@example.com").first()
    if not user:
        print("User not found")
        return
        
    print(f"User ID: {user.id}")
    
    identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == user.id).first()
    if not identity:
        print("GitHubIdentity NOT FOUND")
        return
        
    print(f"GitHub Login: {identity.github_login}")
    print(f"GitHub User ID: {identity.github_user_id}")
    
    cred = db.query(GitHubCredential).filter(GitHubCredential.github_identity_id == identity.id).first()
    if not cred:
        print("GitHubCredential NOT FOUND")
        return
        
    print(f"Credential ID: {cred.id}")
    if cred.encrypted_access_token.startswith("g"):
        print("WARNING: Token appears to be unencrypted")
    else:
        print("Token is encrypted")
        
    # Check repos
    repos = db.query(Repository).all()
    print(f"\nConnected Repositories: {len(repos)}")
    for r in repos:
        print(f"  Repo: {r.github_owner}/{r.github_name} (Branch: {r.default_branch})")

if __name__ == "__main__":
    verify()
