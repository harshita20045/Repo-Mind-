from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes.health import router as health_router
from backend.app.auth.routes import router as auth_router
from backend.app.organizations.routes import router as orgs_router
from backend.app.github.routes import router as github_router

app = FastAPI(
    title="RepoMind Backend",
    description="RepoMind API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(orgs_router)
app.include_router(github_router)