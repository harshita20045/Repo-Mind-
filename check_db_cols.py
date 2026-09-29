import psycopg2

conn = psycopg2.connect('postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='webhook_event' ORDER BY ordinal_position")
print("webhook_event columns:", [r[0] for r in cur.fetchall()])

# Also check alembic current revision
cur.execute("SELECT version_num FROM alembic_version")
print("Alembic revision:", cur.fetchone())
conn.close()
