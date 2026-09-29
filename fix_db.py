import psycopg2
conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
conn.autocommit = True
cur = conn.cursor()
cur.execute("UPDATE review_run SET status='completed' WHERE id=5")
print('Updated ID 5')
