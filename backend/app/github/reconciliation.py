import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.organizations.models import Repository
from backend.app.github.models import PullRequest, GitHubIdentity
from backend.app.github.client import GitHubClient, GitHubAPIError, GitHubTransientError
from backend.app.github.encryption import decrypt_token
from backend.app.webhooks.routes import _get_system_user_id_for_repo
from backend.app.github.service import sync_pull_request_details

logger = logging.getLogger(__name__)

def reconcile_pull_requests(db: Session):
    """
    Cron Job (Reconciliation) -> Polls GET /repos/{o}/{r}/pulls
    Compares last_synced_at / head_sha -> Triggers sync if mismatch.
    """
    repos = db.query(Repository).filter(Repository.index_status != "error").all()

    for repo in repos:
        try:
            sys_user_id = _get_system_user_id_for_repo(db, repo.id)
            if not sys_user_id:
                logger.warning(f"No system user configured for repo {repo.id} during reconciliation.")
                continue

            identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == sys_user_id).first()
            if not identity or not identity.credential:
                continue

            pat = decrypt_token(identity.credential.encrypted_access_token)
            client = GitHubClient(pat)
            
            # Fetch active PRs from GitHub
            remote_prs = client.list_pull_requests(repo.github_owner, repo.github_name, state="all", per_page=50)
            
            for remote_pr in remote_prs:
                github_number = remote_pr.get("number")
                remote_head_sha = remote_pr.get("head", {}).get("sha")
                remote_updated_at = remote_pr.get("updated_at")

                local_pr = (
                    db.query(PullRequest)
                    .filter(
                        PullRequest.repository_id == repo.id,
                        PullRequest.github_number == github_number
                    )
                    .first()
                )

                needs_sync = False
                if not local_pr:
                    needs_sync = True
                else:
                    if local_pr.head_sha != remote_head_sha:
                        needs_sync = True
                    # Could also check timestamps or states

                if needs_sync:
                    logger.info(f"Reconciliation: Syncing PR #{github_number} in repo {repo.id}")
                    if not local_pr:
                        # Quick upsert to have an ID for deep sync
                        local_pr = PullRequest(
                            repository_id=repo.id,
                            github_pr_id=str(remote_pr.get("id")),
                            github_number=github_number,
                            title=remote_pr.get("title", "")[:512],
                            state=remote_pr.get("state", "open"),
                            github_author_login=remote_pr.get("user", {}).get("login"),
                            source_branch=remote_pr.get("head", {}).get("ref"),
                            target_branch=remote_pr.get("base", {}).get("ref"),
                            head_sha=remote_head_sha,
                            base_sha=remote_pr.get("base", {}).get("sha"),
                        )
                        db.add(local_pr)
                        db.commit()
                        db.refresh(local_pr)

                    try:
                        sync_pull_request_details(db, local_pr.id, sys_user_id)
                    except Exception as e:
                        logger.error(f"Reconciliation: Failed deep sync for PR #{github_number}: {e}")

        except Exception as e:
            logger.error(f"Reconciliation failed for repo {repo.id}: {e}")
