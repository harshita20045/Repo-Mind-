import re
file_path = 'backend/alembic/versions/476568fc3a70_add_github_integration_models.py'
with open(file_path, 'r') as f:
    content = f.read()

content = re.sub(r"op\.drop_table\('([^']+)'\)", r'op.execute("DROP TABLE IF EXISTS \1 CASCADE")', content)

with open(file_path, 'w') as f:
    f.write(content)
