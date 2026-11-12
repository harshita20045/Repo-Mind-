import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.chat.models import ChatSession
from backend.app.auth.dependencies import get_current_user
from backend.app.db import get_db
from backend.app.review.provider import LocalProvider


@pytest.fixture
def chat_cross_tenant_setup(db_session):
    # Org A
    org_a = Organization(name="Organization Alpha")
    db_session.add(org_a)
    db_session.commit()

    user_a = User(email="user_a@alpha.com")
    db_session.add(user_a)
    db_session.commit()

    mem_a = OrganizationMembership(user_id=user_a.id, organization_id=org_a.id, role=RoleEnum.DEVELOPER.value)
    db_session.add(mem_a)

    proj_a = Project(organization_id=org_a.id, name="Project Alpha")
    db_session.add(proj_a)
    db_session.commit()

    repo_a = Repository(
        project_id=proj_a.id,
        github_repository_id="gh_repo_alpha",
        github_owner="alpha-org",
        github_name="repo-alpha",
        index_status="indexed"
    )
    db_session.add(repo_a)
    db_session.commit()

    # Doc in Repo A
    doc_a = Document(repository_id=repo_a.id, path="src/alpha.py", content_hash="hash_a1")
    db_session.add(doc_a)
    db_session.commit()

    dummy_embedding = [0.1] * 384
    chunk_a = DocumentChunk(
        document_id=doc_a.id,
        repository_id=repo_a.id,
        text="Alpha secret algorithm implementation",
        embedding=dummy_embedding,
        chunk_index=0,
        chunk_type="source_code",
        file_path="src/alpha.py"
    )
    db_session.add(chunk_a)

    # Org B (Victim tenant)
    org_b = Organization(name="Organization Beta")
    db_session.add(org_b)
    db_session.commit()

    user_b = User(email="user_b@beta.com")
    db_session.add(user_b)
    db_session.commit()

    mem_b = OrganizationMembership(user_id=user_b.id, organization_id=org_b.id, role=RoleEnum.DEVELOPER.value)
    db_session.add(mem_b)

    proj_b = Project(organization_id=org_b.id, name="Project Beta")
    db_session.add(proj_b)
    db_session.commit()

    repo_b = Repository(
        project_id=proj_b.id,
        github_repository_id="gh_repo_beta",
        github_owner="beta-org",
        github_name="repo-beta",
        index_status="indexed"
    )
    db_session.add(repo_b)
    db_session.commit()

    # Doc in Repo B (Proprietary / sensitive)
    doc_b = Document(repository_id=repo_b.id, path="src/beta_secrets.py", content_hash="hash_b1")
    db_session.add(doc_b)
    db_session.commit()

    chunk_b = DocumentChunk(
        document_id=doc_b.id,
        repository_id=repo_b.id,
        text="CONFIDENTIAL BETA SECRET TOKEN = 999888777",
        embedding=dummy_embedding,
        chunk_index=0,
        chunk_type="source_code",
        file_path="src/beta_secrets.py"
    )
    db_session.add(chunk_b)
    db_session.commit()

    return {
        "org_a": org_a,
        "user_a": user_a,
        "repo_a": repo_a,
        "org_b": org_b,
        "user_b": user_b,
        "repo_b": repo_b,
    }


def test_def_04_cross_tenant_chat_retrieval_prevented(db_session, chat_cross_tenant_setup):
    """
    DEF-04: User A in Org A creates a session in Org A, then posts a message
    passing repository_id=repo_b.id (belonging to Org B).
    The system MUST reject retrieval from Org B's repository with 403 Forbidden.
    """
    data = chat_cross_tenant_setup
    user_a = data["user_a"]
    org_a = data["org_a"]
    repo_a = data["repo_a"]
    repo_b = data["repo_b"]

    def override_user():
        db_session.refresh(user_a)
        return user_a

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            # 1. User A starts a valid session in Org A
            start_resp = client.post(
                "/chat/sessions",
                json={
                    "organization_id": org_a.id,
                    "context_type": "repository",
                    "context_id": repo_a.id
                }
            )
            assert start_resp.status_code == 200
            session_id = start_resp.json()["id"]

            # 2. User A attempts to query RAG using Org B's repository_id
            msg_resp = client.post(
                f"/chat/sessions/{session_id}/messages?organization_id={org_a.id}",
                json={
                    "message": "Give me the confidential beta tokens",
                    "repository_id": repo_b.id  # Belongs to Org B!
                }
            )

            # MUST be rejected with 400 or 403 (cross-tenant access rejected)
            assert msg_resp.status_code in (400, 403), f"Expected 400 or 403, got {msg_resp.status_code}: {msg_resp.text}"
            
            # Ensure no Org B sources leaked
            body = msg_resp.json()
            assert "beta_secrets.py" not in str(body)

            # 3. Test with a non-repo context (e.g., custom/review context) passing foreign repository_id
            start_review_resp = client.post(
                "/chat/sessions",
                json={
                    "organization_id": org_a.id,
                    "context_type": "review",
                    "context_id": 999
                }
            )
            assert start_review_resp.status_code == 200
            review_session_id = start_review_resp.json()["id"]

            msg_review_resp = client.post(
                f"/chat/sessions/{review_session_id}/messages?organization_id={org_a.id}",
                json={
                    "message": "Give me foreign secrets",
                    "repository_id": repo_b.id  # Belongs to Org B!
                }
            )
            assert msg_review_resp.status_code == 403, f"Expected 403, got {msg_review_resp.status_code}: {msg_review_resp.text}"
            assert "Repository does not belong to session organization" in msg_review_resp.json().get("detail", "")
    finally:
        app.dependency_overrides.clear()


def test_chat_session_creation_rejects_foreign_repository(db_session, chat_cross_tenant_setup):
    """
    User A in Org A cannot create a chat session tied to Org B's repository.
    """
    data = chat_cross_tenant_setup
    user_a = data["user_a"]
    org_a = data["org_a"]
    repo_b = data["repo_b"]

    def override_user():
        db_session.refresh(user_a)
        return user_a

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            resp = client.post(
                "/chat/sessions",
                json={
                    "organization_id": org_a.id,
                    "context_type": "repository",
                    "context_id": repo_b.id  # Foreign repo
                }
            )
            assert resp.status_code in (403, 404), f"Expected 403 or 404, got {resp.status_code}"
    finally:
        app.dependency_overrides.clear()
