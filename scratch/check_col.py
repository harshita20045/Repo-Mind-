import sys
sys.path.insert(0, ".")
from sqlalchemy import create_engine, text
from backend.app.core.config import settings
from sqlalchemy.engine.url import make_url

url = make_url(settings.POSTGRES_URL).set(database="repomind_test").render_as_string(hide_password=False)
eng = create_engine(url)
with eng.connect() as c:
    row = c.execute(text("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'document_chunk' AND column_name = 'embedding'")).fetchone()
    print("Column info:", row)
