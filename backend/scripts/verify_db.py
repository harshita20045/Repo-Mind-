import sys; sys.path.append('.');
from backend.app.db import SessionLocal;
from sqlalchemy import text;
db = SessionLocal();
tables = ['user', 'organization', 'organization_membership', 'project', 'repository', 'pull_request', 'review', 'chat_session', 'document', 'chunk'];
for t in tables:
    try:
        count = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
        print(f'{t}: {count}')
    except Exception as e:
        db.rollback();
        print(f'{t}: ERROR')
