import re

file_path = 'backend/app/github/routes.py'
with open(file_path, 'r') as f:
    content = f.read()

new_route = """
# ---------------------------------------------------------------------------
# POST /pull-requests/{pull_request_id}/sync
# ---------------------------------------------------------------------------

@router.post(
    "/pull-requests/{pull_request_id}/sync",
    response_model=schemas.PullRequestResponse,
    summary="Force a full synchronization of a pull request",
)
def sync_pull_request_details(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    \"\"\"
    Force sync of a pull request's commits, files, reviews, comments, and checks.
    \"\"\"
    pr = service.get_pull_request_by_id(db, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    _assert_repo_access(db, pr.repository_id, current_user.id)

    # Calling the deep sync logic
    synced_pr = service.sync_pull_request_details(db, pull_request_id, current_user.id)
    return synced_pr
"""

with open(file_path, 'a') as f:
    f.write(new_route)
