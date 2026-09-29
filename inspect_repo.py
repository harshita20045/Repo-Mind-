import sys
import os

sys.path.append(os.path.abspath('.'))

from backend.app.db import SessionLocal
from backend.app.organizations.models import Repository, Project
from backend.app.github.models import PullRequest, PullRequestEvent, PullRequestCheck, PullRequestCommit, PullRequestFile, GitHubReview, GitHubComment, AutomationAction

def inspect():
    db = SessionLocal()
    repo = db.query(Repository).filter(Repository.github_name == 'ai-tutor').first()
    if not repo:
        print("Repository ai-tutor not found.")
        return
        
    print(f"Repo ID: {repo.id}")
    print(f"Owner/Name: {repo.github_owner}/{repo.github_name}")
    print(f"Project ID: {repo.project_id}")
    
    project = db.query(Project).filter(Project.id == repo.project_id).first()
    print(f"Organization ID: {project.organization_id}")
    
    # Check related records
    prs = db.query(PullRequest).filter(PullRequest.repository_id == repo.id).count()
    actions = db.query(AutomationAction).filter(AutomationAction.repository_id == repo.id).count()
    
    print(f"Pull Requests: {prs}")
    print(f"Automation Actions: {actions}")
    
    # We can also check Webhooks if there's a Webhook table
    # No explicit Webhook model seems to exist based on my prior knowledge, but let's check events
    
    print("If this repository is deleted, all cascading child records (PRs, commits, reviews, comments, PR files, check runs, etc.) would be deleted because of SQLAlchemy cascading deletes if configured, or it would result in an IntegrityError if foreign keys restrict it.")

if __name__ == "__main__":
    inspect()
