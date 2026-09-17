# Backend application entry point — RepoMind 2.0

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.health import router as health_router
from backend.app.auth.routes import router as auth_router
from backend.app.organizations.routes import router as orgs_router
from backend.app.github.routes import router as github_router
from backend.app.webhooks.routes import router as webhooks_router
from backend.app.analytics.router import router as analytics_router

app = FastAPI(
    title="RepoMind",
    description="RepoMind 2.0 — PR Review, Risk Intelligence, and AI Engineering Platform",
    version="2.0.0",
)

# CORS middleware for local frontend development
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

from backend.app.review.router import router as review_router
from backend.app.chat.routes import router as chat_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(orgs_router)
app.include_router(github_router)
app.include_router(review_router)
app.include_router(webhooks_router)
app.include_router(chat_router)
app.include_router(analytics_router)
from backend.app.ml.routes import router as ml_router
app.include_router(ml_router)



if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
