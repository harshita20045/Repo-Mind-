# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import psycopg2

conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur = conn.cursor()

# Check ALL webhook events
cur.execute("""
    SELECT we.id, we.github_delivery_id, we.event_type, we.action, we.status,
           we.error_message, we.repository_id, we.received_at, we.processed_at
    FROM webhook_event we
    ORDER BY we.id DESC
    LIMIT 10
""")
events = cur.fetchall()
print("All WebhookEvents:")
for e in events:
    print(f"  ID={e[0]} delivery={e[1][:20]}... event={e[2]} action={e[3]} status={e[4]} error={e[5]} repo_id={e[6]}")

# Check PRs for repo 2
cur.execute("""
    SELECT pr.id, pr.repository_id, pr.github_number, pr.title, pr.source_branch,
           pr.target_branch, pr.github_author_login, pr.state
    FROM pull_request pr
    WHERE pr.repository_id = 2
    ORDER BY pr.id DESC
""")
prs = cur.fetchall()
print(f"\nPullRequests for repo_id=2: ({len(prs)} total)")
for p in prs:
    print(f"  ID={p[0]} repo={p[1]} num={p[2]} title={p[3][:50]} branch={p[4]} target={p[5]} author={p[6]} state={p[7]}")

# Check ReviewRuns
cur.execute("""
    SELECT rr.id, rr.pull_request_id, rr.status, rr.progress_message, rr.commit_sha,
           rr.started_at, rr.completed_at
    FROM review_run rr
    ORDER BY rr.id DESC
    LIMIT 10
""")
runs = cur.fetchall()
print(f"\nReviewRuns: ({len(runs)} total)")
for r in runs:
    print(f"  ID={r[0]} pr_id={r[1]} status={r[2]} msg={r[3][:60] if r[3] else 'None'} sha={r[4][:12] if r[4] else 'None'}")

conn.close()
