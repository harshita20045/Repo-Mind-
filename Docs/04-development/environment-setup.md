# Local development environment

RepoMind uses a repository-local `.venv` and the committed frontend lockfile.
The literal `%VENV%` directory was an obsolete virtual environment tied to a
missing local Python installation and is intentionally not part of the project.

## Backend

From the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Copy `.env.example` to `.env` and provide a PostgreSQL connection, JWT secret,
and Fernet key before running migrations or the API. Tests require a separate
`repomind_test` PostgreSQL database with the `vector` extension available.

## Frontend

```powershell
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
```

## Cookie security

`ENVIRONMENT=production` or `staging` enables the `Secure` session-cookie flag
by default. Local development and tests remain compatible with HTTP. Override
this only through `COOKIE_SECURE` when the deployment transport is intentional.
