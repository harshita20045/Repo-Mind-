import re

file_path = 'backend/app/github/service.py'
with open(file_path, 'r') as f:
    content = f.read()

events_logic = """
    # 6. Sync Events (Phase 11)
    from backend.app.github.models import PullRequestEvent
    raw_events = client.list_pull_request_events(owner, name, number)
    
    # Simple strategy: clear and recreate (or we could deduplicate by a composite of actor/type/timestamp)
    # But GitHub Issue Events don't have stable global IDs in the same way, though they do have 'id'.
    # Actually, GitHub Issue Events *do* have 'id'. Let's check if the payload has an 'id'.
    # We will just parse them. To prevent duplicates, we can look up existing by event type and timestamp,
    # or just wipe and recreate for simplicity during sync.
    # We will use wipe and recreate for events since they are just a log and we don't hold foreign keys to them.
    db.query(PullRequestEvent).filter(PullRequestEvent.pull_request_id == pr.id).delete()
    
    import json
    for revent in raw_events:
        evt = PullRequestEvent(
            pull_request_id=pr.id,
            event_type=revent.get("event"),
            actor_login=revent.get("actor", {}).get("login") if revent.get("actor") else None,
            commit_sha=revent.get("commit_id"),
        )
        created_at_str = revent.get("created_at")
        if created_at_str:
            evt.timestamp = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            
        # Store a minimal payload if needed
        payload_dict = {
            k: v for k, v in revent.items() 
            if k not in ("actor", "event", "commit_id", "created_at", "url", "issue")
        }
        evt.payload = json.dumps(payload_dict) if payload_dict else None
        
        db.add(evt)
        
    db.commit()
"""

# We'll insert this just before `db.commit()` at the end of sync_pull_request_details.
# Let's find the `db.commit()` in `sync_pull_request_details`
pattern = r"            chk\.url = run\.get\(\"html_url\"\)\n\s+db\.commit\(\)\n\s+db\.refresh\(pr\)"
replacement = r"            chk.url = run.get(\"html_url\")\n\n" + events_logic + "\n    db.refresh(pr)"

content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(content)
