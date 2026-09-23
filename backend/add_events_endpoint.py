import re

file_path = 'backend/app/github/routes.py'
with open(file_path, 'r') as f:
    content = f.read()

events_endpoint = """
@router.get("/pull-requests/{pull_request_id}/events")
def get_pull_request_events(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    \"\"\"Get the activity history of a pull request.\"\"\"
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    _assert_repo_access(db, current_user.id, pr.repository_id)

    from backend.app.github.models import PullRequestEvent
    events = (
        db.query(PullRequestEvent)
        .filter(PullRequestEvent.pull_request_id == pull_request_id)
        .order_by(PullRequestEvent.timestamp.desc())
        .all()
    )
    
    # Let's map it into a dict
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "actor_login": e.actor_login,
            "commit_sha": e.commit_sha,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "payload": e.payload
        } for e in events
    ]
"""

with open(file_path, 'a') as f:
    f.write("\n" + events_endpoint + "\n")
