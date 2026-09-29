# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import psycopg2

conn = psycopg2.connect('postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db')
cur = conn.cursor()

# All webhook events
cur.execute('SELECT id, event_type, action, status, github_delivery_id FROM webhook_event ORDER BY id')
print("All Webhook Events:")
for r in cur.fetchall():
    print(f"  {r}")

# All ReviewRuns with their PR numbers
cur.execute("""
    SELECT rr.id, rr.pull_request_id, pr.github_number, rr.status, rr.started_at
    FROM review_run rr
    JOIN pull_request pr ON pr.id = rr.pull_request_id
    ORDER BY rr.id
""")
print("\nAll ReviewRuns:")
for r in cur.fetchall():
    print(f"  RunID={r[0]} pr_id={r[1]} PR#{r[2]} status={r[3]} started={r[4]}")

conn.close()
