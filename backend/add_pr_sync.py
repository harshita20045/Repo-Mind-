import re

service_path = 'backend/app/github/service.py'
with open(service_path, 'r') as f:
    content = f.read()

pr_sync_logic = """
def sync_pull_request_details(db: Session, pr_id: int, user_id: int) -> PullRequest:
    from backend.app.github.models import (
        PullRequestCommit, PullRequestFile, GitHubReview, GitHubComment, PullRequestCheck
    )
    
    pr = get_pull_request_by_id(db, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
        
    repo = pr.repository
    pat = get_decrypted_pat_for_user(db, user_id)
    client = GitHubClient(pat)
    owner = repo.github_owner
    name = repo.github_name
    number = pr.github_number

    # 1. Sync Commits
    raw_commits = client.list_pull_request_commits(owner, name, number)
    existing_commits = {c.sha: c for c in pr.commits}
    for idx, rc in enumerate(raw_commits):
        sha = rc.get("sha")
        c = existing_commits.get(sha)
        if not c:
            c = PullRequestCommit(
                pull_request_id=pr.id,
                sha=sha,
            )
            db.add(c)
        c.author = rc.get("commit", {}).get("author", {}).get("name")
        c.committer = rc.get("commit", {}).get("committer", {}).get("name")
        c.message = rc.get("commit", {}).get("message")
        parents = rc.get("parents", [])
        c.parent_shas = ",".join([p.get("sha") for p in parents]) if parents else None
        c.github_url = rc.get("html_url")
        c.sequence = idx
        
    # 2. Sync Files
    raw_files = client.get_pull_request_files(owner, name, number)
    existing_files = {f.file_path: f for f in pr.files}
    for rf in raw_files:
        f_path = rf.get("filename")
        f = existing_files.get(f_path)
        if not f:
            f = PullRequestFile(
                pull_request_id=pr.id,
                file_path=f_path,
            )
            db.add(f)
        f.status = rf.get("status")
        f.additions = rf.get("additions")
        f.deletions = rf.get("deletions")
        f.changes = rf.get("changes")
        f.previous_filename = rf.get("previous_filename")
        f.blob_url = rf.get("blob_url")
        f.raw_url = rf.get("raw_url")
        f.patch_data = rf.get("patch")
        
    # 3. Sync Reviews
    raw_reviews = client.list_pull_request_reviews(owner, name, number)
    existing_reviews = {str(r.github_review_id): r for r in pr.github_reviews}
    for rr in raw_reviews:
        r_id = str(rr.get("id"))
        rv = existing_reviews.get(r_id)
        if not rv:
            rv = GitHubReview(
                pull_request_id=pr.id,
                github_review_id=r_id,
            )
            db.add(rv)
        rv.github_reviewer_login = rr.get("user", {}).get("login")
        rv.commit_sha = rr.get("commit_id")
        rv.state = rr.get("state")
        rv.body = rr.get("body")
        if rr.get("submitted_at"):
            rv.submitted_at = datetime.fromisoformat(rr.get("submitted_at").replace("Z", "+00:00"))

    # 4. Sync Comments
    raw_comments = client.list_pull_request_comments(owner, name, number)
    existing_comments = {str(c.github_comment_id): c for c in pr.github_comments}
    for rc in raw_comments:
        c_id = str(rc.get("id"))
        cm = existing_comments.get(c_id)
        if not cm:
            cm = GitHubComment(
                pull_request_id=pr.id,
                github_comment_id=c_id,
            )
            db.add(cm)
        cm.github_author_login = rc.get("user", {}).get("login")
        cm.commit_sha = rc.get("commit_id")
        cm.body = rc.get("body")
        cm.file_path = rc.get("path")
        cm.line_number = rc.get("line")
        
    # 5. Sync Checks (if head_sha is available)
    if pr.head_sha:
        raw_checks = client.get_pull_request_checks(owner, name, pr.head_sha)
        check_runs = raw_checks.get("check_runs", [])
        existing_checks = {str(cr.github_check_run_id): cr for cr in pr.checks}
        for run in check_runs:
            run_id = str(run.get("id"))
            chk = existing_checks.get(run_id)
            if not chk:
                chk = PullRequestCheck(
                    pull_request_id=pr.id,
                    github_check_run_id=run_id,
                )
                db.add(chk)
            chk.name = run.get("name")
            chk.status = run.get("status")
            chk.conclusion = run.get("conclusion")
            chk.head_sha = run.get("head_sha")
            chk.url = run.get("html_url")
            
    db.commit()
    db.refresh(pr)
    return pr
"""

with open(service_path, 'a') as f:
    f.write(pr_sync_logic)
