import re

file_path = 'backend/app/chat/service.py'
with open(file_path, 'r') as f:
    content = f.read()

pr_context_logic = """
    # PR Specific Context (Phase 17)
    if session.context_type == "pull_request":
        from backend.app.github.models import PullRequest, PullRequestCommit, PullRequestEvent, AIAnalysis, HumanReview
        pr = db.query(PullRequest).filter(PullRequest.id == session.context_id).first()
        if pr:
            pr_info = f"--- PULL REQUEST METADATA ---\n"
            pr_info += f"Title: {pr.title}\\n"
            pr_info += f"Author: {pr.github_author_login}\\n"
            pr_info += f"State: {pr.state}\\n"
            pr_info += f"Target Branch: {pr.target_branch} <- Source Branch: {pr.source_branch}\\n"
            pr_info += f"Head SHA: {pr.head_sha}\\n\\n"
            
            ai = db.query(AIAnalysis).filter(AIAnalysis.pull_request_id == pr.id).order_by(AIAnalysis.completed_at.desc()).first()
            if ai:
                stale_flag = " (STALE)" if ai.commit_sha != pr.head_sha else " (CURRENT)"
                pr_info += f"--- LATEST AI ANALYSIS{stale_flag} ---\\nCommit: {ai.commit_sha}\\nStatus: {ai.status}\\n\\n"
            
            hr = db.query(HumanReview).filter(HumanReview.pull_request_id == pr.id).order_by(HumanReview.id.desc()).first()
            if hr:
                stale_flag = " (STALE)" if hr.commit_sha != pr.head_sha else " (CURRENT)"
                pr_info += f"--- LATEST HUMAN REVIEW{stale_flag} ---\\nCommit: {hr.commit_sha}\\nDecision: {hr.decision}\\n\\n"
                
            evidence_parts.insert(0, pr_info)
"""

# Find `# 3. Build evidence string` and insert after the loop.
# We'll replace:
#     evidence_text = "\n".join(evidence_parts) if evidence_parts else "No relevant repository context found."
# with our new logic plus the join.

pattern = r"    evidence_text = \"\\n\"\.join\(evidence_parts\) if evidence_parts else \"No relevant repository context found\.\""
replacement = pr_context_logic + "\n    evidence_text = \"\\n\".join(evidence_parts) if evidence_parts else \"No relevant repository context found.\""

content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(content)
