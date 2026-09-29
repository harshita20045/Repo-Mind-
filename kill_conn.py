import psycopg2
conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'repomind_test'")
