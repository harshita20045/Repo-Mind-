# Backend application entry point

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.health import router as health_router
from backend.app.auth.routes import router as auth_router
from backend.app.organizations.routes import router as orgs_router


app = FastAPI(
    title="RepoMind Backend",
    description="RepoMind API - RAG-grounded PR review and risk intelligence platform",
    version="0.1.0",
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

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(orgs_router)


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
