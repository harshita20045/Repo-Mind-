"""
Comprehensive API Route & Authorization Tests for Onboarding Endpoints — Step 3.

Covers:
1. Authorized user can retrieve blueprint (REPOS_READ).
2. User without REPOS_READ cannot retrieve blueprint.
3. User without REPOS_INDEX cannot refresh blueprint.
4. User below Team Lead cannot refresh blueprint.
5. Team Lead+ can refresh blueprint.
6. Unauthenticated requests return 401.
7. User can retrieve their own progress.
8. User cannot retrieve another user's progress.
9. User cannot update another user's progress by injecting user ID.
10. Invalid track and milestone IDs are rejected with 422.
11. Repository access enforced for all four endpoints.
12. Active generation conflicts return 409 Conflict.
13. Unindexed repository errors return 400 Bad Request safely.
14. Responses do not leak internal prompts, exception traces, or sensitive fields.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress
from backend.app.onboarding.service import GenerationInProgressError, UnindexedRepositoryError


@pytest.fixture
def route_test_setup(db_session):
    # Org 1 with project and repository
    org = Organization(name="Route Test Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Route Test Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-route-repo-1",
        github_owner="test-owner",
        github_name="test-route-repo",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(repo)
    db_session.flush()

    # Seed an indexed document
    doc = Document(repository_id=repo.id, path="backend/app/main.py", content_hash="hash123")
    db_session.add(doc)

    # Seed an existing ready blueprint
    bp = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="a" * 40,
        status="ready",
        summary="A production-grade application architecture.",
        architecture_pattern="Modular Monolith",
        subsystems=[
            {"name": "API", "path": "backend/app", "purpose": "Routing layer", "key_files": ["backend/app/main.py"]}
        ],
        request_flow=[
            {"step_number": 1, "layer": "Routing", "file": "backend/app/main.py", "symbol": "app", "description": "Entry"}
        ],
        tracks={
            "backend": {
                "track_name": "backend",
                "reading_order": [
                    {"file_path": "backend/app/main.py", "role": "Entry", "why_read": "Boots application", "focus_symbols": ["app"]}
                ],
                "milestones": [
                    {"id": "be_setup", "title": "Run tests", "description": "Verify local setup", "action_type": "run_command", "action_hint": "pytest"}
                ]
            },
            "frontend": {
                "track_name": "frontend",
                "reading_order": [
                    {"file_path": "backend/app/main.py", "role": "Entry", "why_read": "Inspect API", "focus_symbols": ["app"]}
                ],
                "milestones": [
                    {"id": "fe_setup", "title": "Run dev", "description": "Verify dev server", "action_type": "run_command", "action_hint": "npm dev"}
                ]
            },
            "fullstack": {
                "track_name": "fullstack",
                "reading_order": [
                    {"file_path": "backend/app/main.py", "role": "Entry", "why_read": "Inspect fullstack", "focus_symbols": ["app"]}
                ],
                "milestones": [
                    {"id": "fs_setup", "title": "Run all", "description": "Verify full system", "action_type": "first_task", "action_hint": "curl /health"}
                ]
            }
        },
        caution_zones=[
            {"path": "backend/app", "risk_level": "medium", "reason": "Core routes"}
        ],
        safe_starter_areas=[
            {"area": "Tests", "description": "Unit testing", "starter_ideas": ["Add test"]}
        ],
        mermaid_diagram="flowchart TD\n    A[Client] --> B[API]",
    )
    db_session.add(bp)

    # Org 2 (isolated org for cross-org testing)
    other_org = Organization(name="Other Isolated Org")
    db_session.add(other_org)
    db_session.flush()

    other_project = Project(organization_id=other_org.id, name="Other Project")
    db_session.add(other_project)
    db_session.flush()

    other_repo = Repository(
        project_id=other_project.id,
        github_repository_id="gh-other-repo",
        github_owner="other-owner",
        github_name="other-repo",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(other_repo)

    # Users with different roles
    dev_user = User(email="dev@example.com")
    reviewer_user = User(email="reviewer@example.com")
    team_lead_user = User(email="lead@example.com")
    admin_user = User(email="admin@example.com")
    outsider_user = User(email="outsider@example.com")

    db_session.add_all([dev_user, reviewer_user, team_lead_user, admin_user, outsider_user])
    db_session.flush()

    # Memberships in org 1
    db_session.add(OrganizationMembership(user_id=dev_user.id, organization_id=org.id, role=RoleEnum.DEVELOPER))
    db_session.add(OrganizationMembership(user_id=reviewer_user.id, organization_id=org.id, role=RoleEnum.REVIEWER))
    db_session.add(OrganizationMembership(user_id=team_lead_user.id, organization_id=org.id, role=RoleEnum.TEAM_LEAD))
    db_session.add(OrganizationMembership(user_id=admin_user.id, organization_id=org.id, role=RoleEnum.ORG_ADMIN))
    # Outsider belongs ONLY to other_org
    db_session.add(OrganizationMembership(user_id=outsider_user.id, organization_id=other_org.id, role=RoleEnum.DEVELOPER))

    db_session.commit()

    return {
        "org": org,
        "repo": repo,
        "other_repo": other_repo,
        "dev_user": dev_user,
        "reviewer_user": reviewer_user,
        "team_lead_user": team_lead_user,
        "admin_user": admin_user,
        "outsider_user": outsider_user,
    }


def make_client_for_user(db_session, user):
    """Create a TestClient with overridden get_current_user and get_db."""
    def _override_get_current_user():
        db_session.refresh(user)
        return user

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def cleanup_overrides():
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_1_authorized_user_can_retrieve_blueprint(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        response = client.get(f"/repositories/{setup['repo'].id}/onboarding/blueprint")
        assert response.status_code == 200
        data = response.json()
        assert data["repository_id"] == setup["repo"].id
        assert data["status"] == "ready"
        assert data["architecture_pattern"] == "Modular Monolith"
        assert "backend" in data["tracks"]
    finally:
        cleanup_overrides()


def test_2_user_without_repos_read_cannot_retrieve_blueprint(route_test_setup, db_session):
    setup = route_test_setup
    # Outsider is not a member of the repository's organization
    client = make_client_for_user(db_session, setup["outsider_user"])
    try:
        response = client.get(f"/repositories/{setup['repo'].id}/onboarding/blueprint")
        assert response.status_code in (403, 404)
    finally:
        cleanup_overrides()


def test_3_user_without_repos_index_cannot_refresh(route_test_setup, db_session):
    setup = route_test_setup
    # Developer does NOT have REPOS_INDEX
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        response = client.post(f"/repositories/{setup['repo'].id}/onboarding/blueprint/refresh")
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"] or "requires" in response.json()["detail"]
    finally:
        cleanup_overrides()


def test_4_user_below_team_lead_cannot_refresh(route_test_setup, db_session):
    setup = route_test_setup
    # Reviewer does not have Team Lead role
    client = make_client_for_user(db_session, setup["reviewer_user"])
    try:
        response = client.post(f"/repositories/{setup['repo'].id}/onboarding/blueprint/refresh")
        assert response.status_code == 403
    finally:
        cleanup_overrides()


def test_5_team_lead_and_admin_can_refresh(route_test_setup, db_session):
    setup = route_test_setup

    with patch("backend.app.onboarding.service.OnboardingService.get_or_generate_blueprint") as mock_gen:
        from backend.app.onboarding.schemas import RepositoryBlueprintResponse
        mock_gen.return_value = RepositoryBlueprintResponse(
            repository_id=setup["repo"].id,
            analyzed_commit_sha="b" * 40,
            status="ready",
            architecture_pattern="Modular Monolith",
            summary="Refreshed",
        )

        # Team Lead
        client_lead = make_client_for_user(db_session, setup["team_lead_user"])
        try:
            resp = client_lead.post(f"/repositories/{setup['repo'].id}/onboarding/blueprint/refresh")
            assert resp.status_code == 200
            assert resp.json()["analyzed_commit_sha"] == "b" * 40
        finally:
            cleanup_overrides()

        # Org Admin
        client_admin = make_client_for_user(db_session, setup["admin_user"])
        try:
            resp = client_admin.post(f"/repositories/{setup['repo'].id}/onboarding/blueprint/refresh")
            assert resp.status_code == 200
        finally:
            cleanup_overrides()


def test_6_unauthenticated_requests_are_rejected(route_test_setup):
    cleanup_overrides()
    client = TestClient(app)
    response = client.get(f"/repositories/{route_test_setup['repo'].id}/onboarding/blueprint")
    assert response.status_code == 401


def test_7_user_can_retrieve_own_progress(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        response = client.get(f"/repositories/{setup['repo'].id}/onboarding/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["repository_id"] == setup["repo"].id
        assert data["active_track"] == "backend"
        assert data["completed_milestones"] == []
    finally:
        cleanup_overrides()


def test_8_user_cannot_retrieve_another_users_progress(route_test_setup, db_session):
    setup = route_test_setup
    # Create progress for dev_user
    db_session.add(UserOnboardingProgress(
        user_id=setup["dev_user"].id,
        repository_id=setup["repo"].id,
        active_track="backend",
        completed_milestones=["be_setup"],
        notes="Secret dev notes",
    ))
    db_session.commit()

    # When team_lead calls GET /progress, they get THEIR OWN progress, not dev_user's
    client = make_client_for_user(db_session, setup["team_lead_user"])
    try:
        response = client.get(f"/repositories/{setup['repo'].id}/onboarding/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] != "Secret dev notes"
    finally:
        cleanup_overrides()


def test_9_user_cannot_update_another_user_by_injecting_user_id(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        # Client attempts to pass user_id in payload; schema forbids extra fields
        response = client.put(
            f"/repositories/{setup['repo'].id}/onboarding/progress",
            json={"user_id": setup["admin_user"].id, "active_track": "frontend"},
        )
        assert response.status_code == 422
    finally:
        cleanup_overrides()


def test_10_invalid_track_and_milestone_ids_are_rejected(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        # Invalid track
        resp1 = client.put(
            f"/repositories/{setup['repo'].id}/onboarding/progress",
            json={"active_track": "invalid_track_name"},
        )
        assert resp1.status_code == 422

        # Malformed milestone ID (contains illegal characters)
        resp2 = client.put(
            f"/repositories/{setup['repo'].id}/onboarding/progress",
            json={"completed_milestones": ["bad id with spaces!"]},
        )
        assert resp2.status_code == 422

        # Unknown milestone ID not defined in blueprint
        resp3 = client.put(
            f"/repositories/{setup['repo'].id}/onboarding/progress",
            json={"completed_milestones": ["nonexistent_milestone_999"]},
        )
        assert resp3.status_code == 422
        assert "not found in blueprint" in resp3.json()["detail"]
    finally:
        cleanup_overrides()


def test_11_repository_access_enforced_across_all_endpoints(route_test_setup, db_session):
    setup = route_test_setup
    # Outsider tries to access Org 1's repository
    client = make_client_for_user(db_session, setup["outsider_user"])
    try:
        repo_id = setup["repo"].id
        assert client.get(f"/repositories/{repo_id}/onboarding/blueprint").status_code in (403, 404)
        assert client.post(f"/repositories/{repo_id}/onboarding/blueprint/refresh").status_code in (403, 404)
        assert client.get(f"/repositories/{repo_id}/onboarding/progress").status_code in (403, 404)
        assert client.put(f"/repositories/{repo_id}/onboarding/progress", json={"active_track": "backend"}).status_code in (403, 404)
    finally:
        cleanup_overrides()


def test_12_active_generation_conflict_returns_409(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["team_lead_user"])
    try:
        with patch("backend.app.onboarding.service.OnboardingService.get_or_generate_blueprint") as mock_gen:
            mock_gen.side_effect = GenerationInProgressError("Generation in progress")
            response = client.post(f"/repositories/{setup['repo'].id}/onboarding/blueprint/refresh")
            assert response.status_code == 409
            assert "Generation in progress" in response.json()["detail"]
    finally:
        cleanup_overrides()


def test_13_unindexed_repository_error_returns_400(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        with patch("backend.app.onboarding.service.OnboardingService.get_or_generate_blueprint") as mock_gen:
            mock_gen.side_effect = UnindexedRepositoryError("Repository is not indexed")
            response = client.get(f"/repositories/{setup['repo'].id}/onboarding/blueprint")
            assert response.status_code == 400
            assert "Repository is not indexed" in response.json()["detail"]
    finally:
        cleanup_overrides()


def test_14_responses_do_not_leak_internal_prompts_or_traces(route_test_setup, db_session):
    setup = route_test_setup
    client = make_client_for_user(db_session, setup["dev_user"])
    try:
        response = client.get(f"/repositories/{setup['repo'].id}/onboarding/blueprint")
        assert response.status_code == 200
        raw_text = response.text
        # Assert no prompt instructions or stack traces leaked
        assert "CRITICAL GROUNDING RULES" not in raw_text
        assert "Traceback" not in raw_text
        assert "password_hash" not in raw_text
    finally:
        cleanup_overrides()

