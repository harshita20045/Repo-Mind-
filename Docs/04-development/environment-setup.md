# Local development environment

RepoMind 2.0 strictly runs on bare-metal or VMs. Docker is NOT used.
RepoMind uses a repository-local `.venv` and the committed frontend lockfile.

## Backend

From the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### PostgreSQL & pgvector
You must have PostgreSQL running locally on port 5432.
Since RepoMind 2.0 uses Code-Aware RAG, you MUST install the `pgvector` extension natively on your Windows PostgreSQL server:
1. Download or build the pre-compiled Windows pgvector binaries.
2. Install them into your PostgreSQL `share/extension` folder.
3. Start the PostgreSQL server.

### Environment Configuration
Copy `.env.example` to `.env` and fill it out. The following are required:
- `POSTGRES_URL`: `postgresql://postgres:<your_password>@localhost:5432/repomind`
- `LLM_PROVIDER`: `gemini`
- `GEMINI_API_KEY`: Your Google Gemini API Key

Once configured and pgvector is installed, run database migrations:
```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Frontend

The frontend uses Vite, React, and TanStack query.

```powershell
cd frontend
npm ci
npm run dev
```

## Running the Application
The backend and frontend can be started using the provided batch scripts in the root directory:
- `start_backend.bat`
- `start_worker.bat` (Starts the async task queue)
- `start_frontend.bat`
