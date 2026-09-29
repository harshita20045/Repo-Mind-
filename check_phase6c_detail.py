# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import psycopg2

conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur = conn.cursor()

# Detailed ReviewRun inspection for PR ID=9
cur.execute("""
    SELECT rr.id, rr.pull_request_id, rr.status, rr.progress_message,
           rr.commit_sha, rr.started_at, rr.completed_at
    FROM review_run rr
    WHERE rr.pull_request_id = 9
    ORDER BY rr.id ASC
""")
runs = cur.fetchall()
print(f"ReviewRuns for PR ID=9 (PR #11):")
for r in runs:
    print(f"  Run ID={r[0]}")
    print(f"    PR ID:        {r[1]}")
    print(f"    Status:       {r[2]}")
    print(f"    Progress:     {r[3]}")
    print(f"    Commit SHA:   {r[4]}")
    print(f"    Started At:   {r[5]}")
    print(f"    Completed At: {r[6]}")
    print()

# Check findings for the completed run
cur.execute("""
    SELECT f.id, f.review_run_id, f.severity, f.category, f.message
    FROM finding f
    WHERE f.review_run_id IN (SELECT id FROM review_run WHERE pull_request_id = 9)
    ORDER BY f.id
""")
findings = cur.fetchall()
print(f"Findings for PR #11 ReviewRuns: ({len(findings)} total)")
for f in findings:
    print(f"  Finding ID={f[0]} run_id={f[1]} severity={f[2]} category={f[3]}")
    print(f"    Message: {f[4][:100] if f[4] else 'None'}...")

# Verify there are exactly 0 or 1 pending/running runs now
cur.execute("""
    SELECT COUNT(*) FROM review_run 
    WHERE pull_request_id = 9 AND status IN ('pending', 'running')
""")
active = cur.fetchone()[0]
print(f"\nActive (pending/running) ReviewRuns for PR #11: {active}")

# Check webhook event for PR #11
cur.execute("""
    SELECT we.id, we.github_delivery_id, we.event_type, we.action, we.status,
           we.processed_at
    FROM webhook_event we
    WHERE we.event_type = 'pull_request' AND we.repository_id = 2
    ORDER BY we.id DESC
""")
events = cur.fetchall()
print(f"\nPull request WebhookEvents:")
for e in events:
    print(f"  ID={e[0]} delivery={e[1]} action={e[2]} status={e[4]} processed_at={e[5]}")

conn.close()
