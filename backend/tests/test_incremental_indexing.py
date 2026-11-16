import pytest
from sqlalchemy import select
from backend.app.organizations.models import Project, Repository
from backend.app.auth.models import Organization
from backend.app.rag.models import Document, DocumentChunk
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    PackageDependency,
    RepositoryScanSummary,
)
from backend.app.intelligence.indexer import RepositoryIndexer


def test_incremental_indexing_lifecycle(db_session):
    # Setup test repository
    org = Organization(name="Test Org Inc")
    db_session.add(org)
    db_session.commit()

    proj = Project(organization_id=org.id, name="Test Proj Inc")
    db_session.add(proj)
    db_session.commit()

    repo = Repository(
        project_id=proj.id,
        github_owner="acme",
        github_name="intelligence_repo",
        github_repository_id="99902",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()

    indexer = RepositoryIndexer(db_session, repo.id)

    # 1. Initial State: 3 files
    initial_files = {
        "backend/main.py": (
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            "@app.get('/status')\n"
            "def get_status():\n"
            "    return {'status': 'ok'}\n"
        ),
        "frontend/src/App.jsx": (
            "import React from 'react';\n"
            "export default function App() {\n"
            "    return <div>RepoMind</div>;\n"
            "}\n"
        ),
        "README.md": "# Acme Platform\n\nComprehensive repository intelligence platform.\n",
        "requirements.txt": "fastapi>=0.115.0\nsqlalchemy>=2.0.0\n",
        "package.json": '{"dependencies": {"react": "^18.2.0"}}',
    }

    res1 = indexer.index_from_file_dict(initial_files, commit_sha="commit_sha_1")

    assert res1["status"] == "indexed"
    assert res1["added_files"] == 5
    assert res1["modified_files"] == 0
    assert res1["deleted_files"] == 0
    assert res1["symbols_count"] > 0
    assert res1["dependencies_count"] == 3  # 2 pypi + 1 npm

    # Verify Summary created
    summary = db_session.execute(
        select(RepositoryScanSummary).where(RepositoryScanSummary.repository_id == repo.id)
    ).scalar_one_or_none()
    assert summary is not None
    assert summary.scanned_commit_sha == "commit_sha_1"
    assert "FastAPI" in summary.frameworks

    # Verify Chunks created
    chunks_count = db_session.query(DocumentChunk).filter(DocumentChunk.repository_id == repo.id).count()
    assert chunks_count > 0

    # 2. Re-index unchanged repository: Idempotent & Zero-cost
    res2 = indexer.index_from_file_dict(initial_files, commit_sha="commit_sha_1")
    assert res2["added_files"] == 0
    assert res2["modified_files"] == 0
    assert res2["deleted_files"] == 0
    assert res2["unchanged_files"] == 5
    assert res2["chunks_created"] == 0

    # 3. Incremental update: Modify 1 file, add 1 file, delete 1 file
    updated_files = dict(initial_files)
    # Delete README.md
    del updated_files["README.md"]
    # Modify backend/main.py
    updated_files["backend/main.py"] = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/status')\n"
        "def get_status():\n"
        "    return {'status': 'v2_updated'}\n"
        "@app.get('/metrics')\n"
        "def get_metrics():\n"
        "    return {'uptime': 100}\n"
    )
    # Add new file
    updated_files["backend/utils.py"] = (
        "def compute_hash(val: str) -> str:\n"
        "    return str(hash(val))\n"
    )

    res3 = indexer.index_from_file_dict(updated_files, commit_sha="commit_sha_2")

    assert res3["added_files"] == 1       # backend/utils.py
    assert res3["modified_files"] == 1    # backend/main.py
    assert res3["deleted_files"] == 1     # README.md
    assert res3["unchanged_files"] == 3   # frontend/src/App.jsx, requirements.txt, package.json

    # Verify deleted file is gone from DB
    deleted_doc = db_session.execute(
        select(Document).where(Document.repository_id == repo.id, Document.path == "README.md")
    ).scalar_one_or_none()
    assert deleted_doc is None

    # Verify new file exists in DB
    new_doc = db_session.execute(
        select(Document).where(Document.repository_id == repo.id, Document.path == "backend/utils.py")
    ).scalar_one_or_none()
    assert new_doc is not None

    # Verify new symbol node was added
    hash_node = db_session.execute(
        select(CodeGraphNode).where(
            CodeGraphNode.repository_id == repo.id,
            CodeGraphNode.name == "compute_hash"
        )
    ).scalar_one_or_none()
    assert hash_node is not None
