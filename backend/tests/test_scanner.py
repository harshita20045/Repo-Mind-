import pytest
from backend.app.intelligence.scanner import RepositoryScanner


def test_scanner_exclusion_rules():
    scanner = RepositoryScanner()

    # Directories that must be excluded
    assert scanner.should_exclude("node_modules/react/index.js") is True
    assert scanner.should_exclude("backend/__pycache__/main.cpython-313.pyc") is True
    assert scanner.should_exclude(".venv/lib/site-packages/fastapi/__init__.py") is True
    assert scanner.should_exclude("dist/bundle.js") is True
    assert scanner.should_exclude("build/output.css") is True
    assert scanner.should_exclude(".git/objects/abc") is True

    # Secret files that must be excluded
    assert scanner.should_exclude(".env") is True
    assert scanner.should_exclude(".env.production") is True
    assert scanner.should_exclude("certs/server.pem") is True
    assert scanner.should_exclude("certs/server.key") is True

    # Binary files that must be excluded
    assert scanner.should_exclude("assets/logo.png") is True
    assert scanner.should_exclude("archive.zip") is True
    assert scanner.should_exclude("app.exe") is True

    # Valid files that must NOT be excluded
    assert scanner.should_exclude("backend/app/main.py") is False
    assert scanner.should_exclude("frontend/src/App.jsx") is False
    assert scanner.should_exclude("README.md") is False
    assert scanner.should_exclude(".env.example") is False
    assert scanner.should_exclude("docker-compose.yml") is False


def test_scanner_language_and_framework_detection():
    scanner = RepositoryScanner()

    files = {
        "backend/app/main.py": (
            "from fastapi import FastAPI\n"
            "from sqlalchemy.orm import Session\n"
            "app = FastAPI()\n"
            "@app.get('/health')\n"
            "def health():\n"
            "    return {'status': 'ok'}\n"
            "if __name__ == '__main__':\n"
            "    pass\n"
        ),
        "backend/app/models.py": (
            "from sqlalchemy import Column, Integer, String\n"
            "from backend.app.db import Base\n"
            "class User(Base):\n"
            "    __tablename__ = 'users'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    name = Column(String)\n"
        ),
        "frontend/src/App.jsx": (
            "import React from 'react';\n"
            "export default function App() {\n"
            "    return <div className='p-4 text-blue-500'>Hello</div>;\n"
            "}\n"
        ),
        "README.md": "# Project RepoMind\n\nAI Engineering Intelligence Platform.\n",
        "package.json": '{"dependencies": {"react": "^18.2.0", "tailwindcss": "^3.0.0"}}',
        "requirements.txt": "fastapi>=0.115.0\nsqlalchemy>=2.0.0\npytest>=8.0.0\n",
    }

    result = scanner.scan_files(files)

    assert result["primary_language"] in ("Python", "JavaScript (React)")
    assert "FastAPI" in result["frameworks"]
    assert "SQLAlchemy" in result["frameworks"]
    assert "React" in result["frameworks"]
    assert "Tailwind CSS" in result["frameworks"]
    assert "Pytest" in result["frameworks"]

    # Entry points
    assert any("main.py" in ep for ep in result["entry_points"])

    # API routes & DB models
    assert any("main.py" in r for r in result["api_route_files"])
    assert any("models.py" in m for m in result["db_model_files"])

    # Stats
    assert result["stats"]["total_files"] >= 5
    assert result["stats"]["total_lines"] > 20
