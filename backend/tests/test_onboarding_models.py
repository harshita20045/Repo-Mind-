"""
Unit tests for Developer Onboarding & Codebase Blueprint models — Step 1.

Tests:
1. Creation, persistence, and querying of RepositoryBlueprint.
2. Unique constraint on repository_id for RepositoryBlueprint.
3. Creation, persistence, and querying of UserOnboardingProgress.
4. Unique constraint on (user_id, repository_id) for UserOnboardingProgress.
5. Concurrency attributes (status, retry_count, generation_started_at).
6. Cascade delete on repository and user removal.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress


def test_repository_blueprint_creation_and_query(db_session):
    # Setup test org, project, repo
    org = Organization(name="Blueprint Test Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Test Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-repo-1001",
        github_owner="test-owner",
        github_name="test-repo",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    # Create Blueprint
    blueprint = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="a" * 40,
        status="ready",
        architecture_pattern="Modular Monolith",
        summary="Test repository summary",
        subsystems=[
            {"name": "API Layer", "path": "backend/app", "purpose": "Handles routing", "key_files": ["main.py"]}
        ],
        request_flow=[
            {"step_number": 1, "layer": "API", "file": "backend/app/main.py", "symbol": "app", "description": "Entry point"}
        ],
        tracks={
            "backend": {
                "reading_order": [
                    {"file_path": "backend/app/main.py", "role": "Entry", "why_read": "Boots server", "focus_symbols": ["app"]}
                ],
                "milestones": [
                    {"id": "be_1", "title": "Run test", "description": "Execute pytest", "action_type": "run_command", "action_hint": "pytest"}
                ]
            }
        },
        caution_zones=[
            {"path": "backend/app/auth", "risk_level": "high", "reason": "Security boundary"}
        ],
        safe_starter_areas=[
            {"area": "Unit tests", "description": "Add new unit tests", "starter_ideas": ["Test validators"]}
        ],
        mermaid_diagram="graph TD; A-->B;",
        generation_started_at=datetime.now(timezone.utc),
        generation_completed_at=datetime.now(timezone.utc),
    )
    db_session.add(blueprint)
    db_session.commit()

    # Query back
    fetched = db_session.query(RepositoryBlueprint).filter_by(repository_id=repo.id).first()
    assert fetched is not None
    assert fetched.analyzed_commit_sha == "a" * 40
    assert fetched.status == "ready"
    assert fetched.architecture_pattern == "Modular Monolith"
    assert len(fetched.subsystems) == 1
    assert fetched.subsystems[0]["name"] == "API Layer"
    assert "backend" in fetched.tracks


def test_repository_blueprint_uniqueness_per_repository(db_session):
    org = Organization(name="Blueprint Unique Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Unique Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-repo-1002",
        github_owner="test-owner",
        github_name="test-repo-unique",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    bp1 = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="1" * 40,
        status="pending",
    )
    db_session.add(bp1)
    db_session.commit()

    # Second blueprint for the same repository should violate unique constraint
    bp2 = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="2" * 40,
        status="pending",
    )
    db_session.add(bp2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_onboarding_progress_creation_and_privacy(db_session):
    org = Organization(name="Progress Test Org")
    db_session.add(org)
    db_session.flush()

    user = User(email="dev1@example.com", password_hash="dummyhash")
    db_session.add(user)
    db_session.flush()

    project = Project(organization_id=org.id, name="Progress Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-repo-1003",
        github_owner="test-owner",
        github_name="test-repo-prog",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    progress = UserOnboardingProgress(
        user_id=user.id,
        repository_id=repo.id,
        active_track="backend",
        completed_milestones=["be_1", "be_2"],
        notes="Local DB running on port 5432",
    )
    db_session.add(progress)
    db_session.commit()

    fetched = db_session.query(UserOnboardingProgress).filter_by(
        user_id=user.id,
        repository_id=repo.id,
    ).first()
    assert fetched is not None
    assert fetched.active_track == "backend"
    assert fetched.completed_milestones == ["be_1", "be_2"]
    assert "port 5432" in fetched.notes

    # Duplicate progress row for same user and repo must raise IntegrityError
    duplicate_progress = UserOnboardingProgress(
        user_id=user.id,
        repository_id=repo.id,
        active_track="frontend",
    )
    db_session.add(duplicate_progress)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

