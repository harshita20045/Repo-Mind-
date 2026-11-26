import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.db import engine
from sqlalchemy import inspect

insp = inspect(engine)

target_tables = [
    'pull_request', 'pull_request_file', 'pull_request_commit', 'pull_request_event',
    'architecture_decision_record', 'historical_commit_record', 'recurring_issue_hotspot',
    'review_run', 'finding', 'finding_evidence', 'human_decision',
    'test_scenario', 'generated_test_case', 'change_impact_analysis',
    'technical_debt_snapshot', 'technical_debt_issue', 'repository_blueprint',
    'document', 'document_chunk'
]

for tbl in target_tables:
    cols = insp.get_columns(tbl)
    fks = insp.get_foreign_keys(tbl)
    col_str = ', '.join([f"{c['name']}:{c['type']}{'(REQ)' if not c['nullable'] else ''}" for c in cols])
    fk_str = ', '.join([f"{fk['constrained_columns']}->{fk['referred_table']}.{fk['referred_columns']}" for fk in fks])
    print(f"=== {tbl} ===")
    print(f"  Cols: {col_str}")
    if fk_str:
        print(f"  FKs:  {fk_str}")
    print()
