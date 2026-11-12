"""
Regression tests for DEF-07: Onboarding Blueprint Snapshot Hash and Cache Invalidation.
Verifies that:
1. Modifying any indexed document (including second or subsequent files) changes the snapshot SHA.
2. Adding or removing indexed documents changes the snapshot SHA.
3. Blueprints are reused when the snapshot is identical (is_outdated = False).
4. Outdated blueprints are flagged is_outdated = True when any indexed document changes.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from backend.app.auth.models import Organization, User
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.onboarding.models import RepositoryBlueprint
from backend.app.onboarding.service import OnboardingService


@pytest.fixture
def onboarding_repo_fixture(db_session):
    org = Organization(name="Snapshot Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Snapshot Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-snapshot-101",
        github_owner="snapshot-owner",
        github_name="snapshot-repo",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(repo)
    db_session.flush()

    doc1 = Document(
        repository_id=repo.id,
        path="backend/app/main.py",
        content_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    doc2 = Document(
        repository_id=repo.id,
        path="backend/app/routes.py",
        content_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()

    return {
        "org": org,
        "project": project,
        "repo": repo,
        "doc1": doc1,
        "doc2": doc2,
    }


def test_snapshot_hash_changes_when_second_file_modified(db_session, onboarding_repo_fixture):
    """
    DEF-07: In the buggy implementation, [:40] truncated only doc1's hash,
    so modifying doc2 had zero effect on the snapshot SHA.
    With the deterministic SHA-256 over all sorted canonical paths & hashes,
    modifying doc2 MUST change snapshot_sha.
    """
    f = onboarding_repo_fixture
    service = OnboardingService(db_session)

    sha_initial, paths_initial, _ = service.get_indexed_snapshot_info(f["repo"].id)
    assert len(sha_initial) == 40
    assert "backend/app/routes.py" in paths_initial

    # Modify ONLY doc2 (second file in sorted order)
    doc2 = f["doc2"]
    doc2.content_hash = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    db_session.commit()

    sha_modified, paths_modified, _ = service.get_indexed_snapshot_info(f["repo"].id)
    assert len(sha_modified) == 40
    assert sha_initial != sha_modified, "Snapshot SHA must change when second file is modified"


def test_snapshot_hash_changes_on_file_addition_and_removal(db_session, onboarding_repo_fixture):
    """Adding or deleting a document must change the snapshot SHA."""
    f = onboarding_repo_fixture
    service = OnboardingService(db_session)

    sha_before, _, _ = service.get_indexed_snapshot_info(f["repo"].id)

    # Add a 3rd document
    doc3 = Document(
        repository_id=f["repo"].id,
        path="backend/app/auth.py",
        content_hash="dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    )
    db_session.add(doc3)
    db_session.commit()

    sha_added, paths_added, _ = service.get_indexed_snapshot_info(f["repo"].id)
    assert sha_before != sha_added
    assert "backend/app/auth.py" in paths_added

    # Remove doc3
    db_session.delete(doc3)
    db_session.commit()

    sha_removed, _, _ = service.get_indexed_snapshot_info(f["repo"].id)
    assert sha_removed == sha_before


def test_blueprint_reuse_and_invalidation(db_session, onboarding_repo_fixture):
    """
    Verify that an identical repository snapshot reuses the blueprint (is_outdated=False),
    and modifying a document marks the cached blueprint as is_outdated=True.
    """
    f = onboarding_repo_fixture
    service = OnboardingService(db_session)
    repo = f["repo"]

    snapshot_sha, _, _ = service.get_indexed_snapshot_info(repo.id)

    # Insert a ready blueprint matched to the current snapshot_sha
    bp = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha=snapshot_sha,
        status="ready",
        summary="A test blueprint summary",
        architecture_pattern="Layered",
        subsystems=[{"name": "Backend", "path": "backend", "purpose": "API", "key_files": []}],
        request_flow=[],
        tracks={
            "backend": {"track_name": "backend", "reading_order": [], "milestones": []},
            "frontend": {"track_name": "frontend", "reading_order": [], "milestones": []},
            "fullstack": {"track_name": "fullstack", "reading_order": [], "milestones": []},
        },
        caution_zones=[],
        safe_starter_areas=[],
        mermaid_diagram="flowchart TD\n    A-->B",
    )
    db_session.add(bp)
    db_session.commit()

    # 1. Fetching blueprint on identical snapshot should return is_outdated == False
    res1 = service.get_or_generate_blueprint(repo.id, force_refresh=False)
    assert res1.is_outdated is False
    assert res1.analyzed_commit_sha == snapshot_sha

    # 2. Modify doc2 content_hash
    f["doc2"].content_hash = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    db_session.commit()

    # 3. Fetching blueprint on modified snapshot should return is_outdated == True
    res2 = service.get_or_generate_blueprint(repo.id, force_refresh=False)
    assert res2.is_outdated is True
    assert res2.analyzed_commit_sha == snapshot_sha
    assert res2.summary == "A test blueprint summary"
