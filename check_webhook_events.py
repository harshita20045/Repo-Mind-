import psycopg2

conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur = conn.cursor()
cur.execute("""
    SELECT 
        we.id,
        we.github_delivery_id,
        we.event_type,
        we.action,
        we.status,
        we.received_at,
        we.repository_id,
        r.github_owner,
        r.github_name
    FROM webhook_event we
    LEFT JOIN repository r ON r.id = we.repository_id
    ORDER BY we.id DESC
    LIMIT 10
""")
rows = cur.fetchall()
print(f"Total recent WebhookEvents: {len(rows)}")
for r in rows:
    print(f"  ID={r[0]} delivery={r[1]} event={r[2]} action={r[3]} status={r[4]} repo_id={r[6]} repo={r[7]}/{r[8]}")
conn.close()
