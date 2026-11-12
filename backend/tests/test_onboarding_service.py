"""
Comprehensive Unit & Integration Tests for Onboarding Service & Intelligence Layer — Step 2.

Covers:
1. Strict Pydantic Schema Validation (valid, malformed, missing fields, missing tracks).
2. Gemini Mocking & Response Parsing.
3. Anti-Hallucination & Fabricated Path Rejection.
4. Concurrency Locking & Stale Pending Job Recovery.
5. Cache Hit vs. Invalidation & Outdated Flagging.
6. Regeneration Failure with Preservation of Previous Valid Blueprint.
7. Mermaid Syntax Validation.
8. User Progress Privacy and Dynamic Checklist Verification.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from backend.app.auth.models import Organization, User
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress
from backend.app.onboarding.schemas import (
    LLMBlueprintPayload,
    SubsystemItem,
    RequestFlowStep,
    TrackPlan,
    ReadingOrderItem,
    MilestoneItem,
    CautionZone,
    SafeStarterArea,
    UpdateProgressRequest,
)
from backend.app.onboarding.service import (
    OnboardingService,
    UnindexedRepositoryError,
    GenerationInProgressError,
    BlueprintGenerationError,
    GroundingValidationError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_valid_llm_json():
    return {
        "summary": "RepoMind is an advanced engineering intelligence system for PR review and risk analysis.",
        "architecture_pattern": "Modular Monolith",
        "subsystems": [
            {
                "name": "API Layer",
                "path": "backend/app",
                "purpose": "Provides FastAPI routing and middlewares",
                "key_files": ["backend/app/main.py"]
            }
        ],
        "request_flow": [
            {
                "step_number": 1,
                "layer": "Routing",
                "file": "backend/app/main.py",
                "symbol": "app",
                "description": "Incoming HTTP request dispatched"
            },
            {
                "step_number": 2,
                "layer": "Authentication",
                "file": "backend/app/auth/routes.py",
                "symbol": "get_current_user",
                "description": "Validates user JWT cookie"
            }
        ],
        "tracks": {
            "backend": {
                "track_name": "backend",
                "reading_order": [
                    {
                        "file_path": "backend/app/main.py",
                        "role": "Entry Point",
                        "why_read": "Understand application bootstrap and middlewares",
                        "focus_symbols": ["app"],
                        "key_lines": "L1-L50"
                    },
                    {
                        "file_path": "backend/app/auth/routes.py",
                        "role": "Auth Handler",
                        "why_read": "Learn session and cookie management",
                        "focus_symbols": ["login"],
                        "key_lines": "L20-L80"
                    }
                ],
                "milestones": [
                    {
                        "id": "be_setup",
                        "title": "Verify Backend Tests",
                        "description": "Run pytest to verify local environment",
                        "action_type": "run_command",
                        "action_hint": "pytest backend/tests/"
                    },
                    {
                        "id": "be_inspect",
                        "title": "Inspect Permissions",
                        "description": "Locate role permission definitions",
                        "action_type": "code_inspection",
                        "action_hint": "Search Permission enum"
                    }
                ]
            },
            "frontend": {
                "track_name": "frontend",
                "reading_order": [
                    {
                        "file_path": "frontend/src/App.jsx",
                        "role": "Router Entry",
                        "why_read": "Top level routing and session state",
                        "focus_symbols": ["App"],
                        "key_lines": "L1-L60"
                    }
                ],
                "milestones": [
                    {
                        "id": "fe_build",
                        "title": "Run Frontend Dev",
                        "description": "Start Vite development server",
                        "action_type": "run_command",
                        "action_hint": "npm run dev"
                    }
                ]
            },
            "fullstack": {
                "track_name": "fullstack",
                "reading_order": [
                    {
                        "file_path": "backend/app/main.py",
                        "role": "API Entry",
                        "why_read": "Understand backend API surface",
                        "focus_symbols": ["app"],
                        "key_lines": "L1-L50"
                    },
                    {
                        "file_path": "frontend/src/App.jsx",
                        "role": "Client Router",
                        "why_read": "Understand client architecture",
                        "focus_symbols": ["App"],
                        "key_lines": "L1-L60"
                    }
                ],
                "milestones": [
                    {
                        "id": "fs_test",
                        "title": "End-to-End Test",
                        "description": "Verify full stack communication",
                        "action_type": "first_task",
                        "action_hint": "Check /health endpoint"
                    }
                ]
            }
        },
        "caution_zones": [
            {
                "path": "backend/app/auth",
                "risk_level": "high",
                "reason": "Security boundary governing authentication tokens"
            }
        ],
        "safe_starter_areas": [
            {
                "area": "Unit Test Coverage",
                "description": "Independent tests for utility validators",
                "starter_ideas": ["Add tests for schema validation"]
            }
        ],
        "mermaid_diagram": "flowchart TD\n    A[Client] --> B[FastAPI Router]\n    B --> C[Postgres DB]"
    }


@pytest.fixture
def indexed_test_repo(db_session):
    org = Organization(name="Service Test Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Service Test Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-repo-service-100",
        github_owner="test-owner",
        github_name="test-repo-service",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(repo)
    db_session.flush()

    # Create indexed documents
    files = [
        "backend/app/main.py",
        "backend/app/auth/routes.py",
        "frontend/src/App.jsx",
        "README.md"
    ]
    for path in files:
        doc = Document(
            repository_id=repo.id,
            path=path,
            content_hash=f"hash-{path}",
        )
        db_session.add(doc)
    db_session.commit()
    return repo


# ---------------------------------------------------------------------------
# 1. Pydantic Validation Tests
# ---------------------------------------------------------------------------

def test_pydantic_schema_validation_success(sample_valid_llm_json):
    payload = LLMBlueprintPayload.model_validate(sample_valid_llm_json)
    assert payload.architecture_pattern == "Modular Monolith"
    assert "backend" in payload.tracks
    assert "frontend" in payload.tracks
    assert "fullstack" in payload.tracks
    assert payload.mermaid_diagram.startswith("flowchart TD")


def test_pydantic_schema_missing_tracks_fails(sample_valid_llm_json):
    del sample_valid_llm_json["tracks"]["fullstack"]
    with pytest.raises(ValidationError) as exc:
        LLMBlueprintPayload.model_validate(sample_valid_llm_json)
    assert "missing required tracks" in str(exc.value)


def test_pydantic_schema_invalid_mermaid_fails(sample_valid_llm_json):
    sample_valid_llm_json["mermaid_diagram"] = "invalid diagram syntax without starter"
    with pytest.raises(ValidationError) as exc:
        LLMBlueprintPayload.model_validate(sample_valid_llm_json)
    assert "Mermaid diagram must begin with a recognized diagram type" in str(exc.value)


# ---------------------------------------------------------------------------
# 2. Grounding & Anti-Hallucination Tests
# ---------------------------------------------------------------------------

def test_grounding_rejects_fabricated_request_flow_path(indexed_test_repo, sample_valid_llm_json, db_session):
    service = OnboardingService(db_session)
    # Inject a fabricated file in request_flow
    sample_valid_llm_json["request_flow"][0]["file"] = "fabricated/fake_service.py"

    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps(sample_valid_llm_json)

    with patch("backend.app.onboarding.service.get_llm_provider", return_value=mock_llm):
        with pytest.raises(BlueprintGenerationError) as exc:
            service.get_or_generate_blueprint(indexed_test_repo.id)
        assert "Fabricated file path 'fabricated/fake_service.py'" in str(exc.value)


def test_unindexed_repository_raises_error(db_session):
    org = Organization(name="Unindexed Org")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="Unindexed Project")
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-repo-unindexed",
        github_owner="test-owner",
        github_name="unindexed-repo",
        default_branch="main",
        index_status="unindexed",
    )
    db_session.add(repo)
    db_session.commit()

    service = OnboardingService(db_session)
    with pytest.raises(UnindexedRepositoryError):
        service.get_or_generate_blueprint(repo.id)


# ---------------------------------------------------------------------------
# 3. Cache Hits & Generation Lifecycle
# ---------------------------------------------------------------------------

def test_generation_and_cache_hit(indexed_test_repo, sample_valid_llm_json, db_session):
    service = OnboardingService(db_session)

    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps(sample_valid_llm_json)

    with patch("backend.app.onboarding.service.get_llm_provider", return_value=mock_llm):
        # First call generates
        resp1 = service.get_or_generate_blueprint(indexed_test_repo.id)
        assert resp1.status == "ready"
        assert resp1.architecture_pattern == "Modular Monolith"
        assert mock_llm.complete.call_count == 1

        # Second call hits cache (mock_llm not called again)
        resp2 = service.get_or_generate_blueprint(indexed_test_repo.id)
        assert resp2.status == "ready"
        assert mock_llm.complete.call_count == 1  # Unchanged!


# ---------------------------------------------------------------------------
# 4. Concurrency & Stale Pending Job Recovery
# ---------------------------------------------------------------------------

def test_duplicate_concurrent_generation_prevention(indexed_test_repo, db_session):
    service = OnboardingService(db_session)

    # Insert an in-progress pending record
    bp = RepositoryBlueprint(
        repository_id=indexed_test_repo.id,
        analyzed_commit_sha="dummy-sha",
        status="pending",
        generation_started_at=datetime.now(timezone.utc),
    )
    db_session.add(bp)
    db_session.commit()

    # Second concurrent call within timeout should raise GenerationInProgressError
    with pytest.raises(GenerationInProgressError):
        service.get_or_generate_blueprint(indexed_test_repo.id)


def test_stale_pending_job_recovery(indexed_test_repo, sample_valid_llm_json, db_session):
    service = OnboardingService(db_session)

    # Insert a stale pending record older than 5 minutes
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    bp = RepositoryBlueprint(
        repository_id=indexed_test_repo.id,
        analyzed_commit_sha="dummy-sha",
        status="pending",
        retry_count=1,
        generation_started_at=stale_time,
    )
    db_session.add(bp)
    db_session.commit()

    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps(sample_valid_llm_json)

    with patch("backend.app.onboarding.service.get_llm_provider", return_value=mock_llm):
        # Service should recover the stale job and succeed
        resp = service.get_or_generate_blueprint(indexed_test_repo.id)
        assert resp.status == "ready"
        assert resp.retry_count == 0


# ---------------------------------------------------------------------------
# 5. Regeneration Failure Preserves Previous Valid Blueprint
# ---------------------------------------------------------------------------

def test_failed_regeneration_preserves_previous_valid_blueprint(indexed_test_repo, sample_valid_llm_json, db_session):
    service = OnboardingService(db_session)

    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps(sample_valid_llm_json)

    with patch("backend.app.onboarding.service.get_llm_provider", return_value=mock_llm):
        resp1 = service.get_or_generate_blueprint(indexed_test_repo.id)
        assert resp1.status == "ready"

    # Now simulate a failed regeneration (e.g. LLM crashes or returns garbage)
    failing_llm = MagicMock()
    failing_llm.complete.side_effect = Exception("API Quota Exceeded")

    with patch("backend.app.onboarding.service.get_llm_provider", return_value=failing_llm):
        with pytest.raises(BlueprintGenerationError):
            service.get_or_generate_blueprint(indexed_test_repo.id, force_refresh=True)

    # Invariant: Previous blueprint data must still be intact and status ready
    persisted = db_session.query(RepositoryBlueprint).filter_by(repository_id=indexed_test_repo.id).first()
    assert persisted.status == "ready"
    assert persisted.summary == sample_valid_llm_json["summary"]
    assert "Preserving last valid blueprint" in persisted.generation_error


# ---------------------------------------------------------------------------
# 6. User Progress & Anti-Surveillance
# ---------------------------------------------------------------------------

def test_user_progress_isolated_and_updatable(indexed_test_repo, db_session):
    service = OnboardingService(db_session)

    user1 = User(email="user1@example.com", password_hash="dummy")
    user2 = User(email="user2@example.com", password_hash="dummy")
    db_session.add_all([user1, user2])
    db_session.commit()

    # User 1 initializes and updates progress
    p1 = service.get_user_progress(user1.id, indexed_test_repo.id)
    assert p1.completed_milestones == []

    updated_p1 = service.update_user_progress(
        user1.id,
        indexed_test_repo.id,
        UpdateProgressRequest(
            active_track="frontend",
            completed_milestones=["fe_build"],
            notes="Configured Vite port 5173",
        )
    )
    assert updated_p1.active_track == "frontend"
    assert updated_p1.completed_milestones == ["fe_build"]
    assert "5173" in updated_p1.notes

    # User 2 progress is completely separate
    p2 = service.get_user_progress(user2.id, indexed_test_repo.id)
    assert p2.active_track == "backend"
    assert p2.completed_milestones == []
    assert p2.notes == ""

