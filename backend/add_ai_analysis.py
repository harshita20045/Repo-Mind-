import re

file_path = 'backend/app/review/service.py'
with open(file_path, 'r') as f:
    content = f.read()

ai_analysis_logic = """
    # Phase 12: Save AIAnalysis(commit_sha)
    from backend.app.github.models import AIAnalysis
    ai_analysis = (
        db.query(AIAnalysis)
        .filter(
            AIAnalysis.pull_request_id == run.pull_request_id,
            AIAnalysis.commit_sha == run.commit_sha
        ).first()
    )
    import json
    findings_json = json.dumps([f.id for f in findings])
    if not ai_analysis:
        ai_analysis = AIAnalysis(
            pull_request_id=run.pull_request_id,
            commit_sha=run.commit_sha,
            status="completed",
            findings=findings_json,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(ai_analysis)
    else:
        ai_analysis.status = "completed"
        ai_analysis.findings = findings_json
        ai_analysis.completed_at = datetime.now(timezone.utc)
"""

# We'll inject this right before db.commit() in execute_review_run, which is around line 180-200.
# Let's find the end of execute_review_run. It ends with:
#     run.status = "completed"
#     run.completed_at = datetime.now(timezone.utc)
#     run.progress_message = None
#     db.commit()

pattern = r"    run\.status = \"completed\"\n    run\.completed_at = datetime\.now\(timezone\.utc\)\n    run\.progress_message = None\n    db\.commit\(\)"
replacement = r"    run.status = \"completed\"\n    run.completed_at = datetime.now(timezone.utc)\n    run.progress_message = None\n\n" + ai_analysis_logic + "\n    db.commit()"

content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(content)
