"""
Tests for RepoMind Smart Developer Onboarding Features:
  - 4 Role-specific learning paths (Backend, Frontend, Fullstack, QA Engineer)
  - 4 Runtime execution flows (Startup, API Lifecycle, Auth & RBAC, Database & ORM)
  - Request lifecycle Mermaid sequenceDiagram
  - Repository domain glossary with file grounding
  - Strict anti-surveillance privacy for developer notes and progress
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress
from backend.app.onboarding.schemas import (
    LLMBlueprintPayload,
    RepositoryBlueprintResponse,
    ExecutionFlows,
    ExecutionFlowStep,
    GlossaryItem,
    TrackPlan,
    ReadingOrderItem,
    MilestoneItem,
    SubsystemItem,
    RequestFlowStep,
    CautionZone,
    SafeStarterArea,
)
from backend.app.onboarding.service import OnboardingService, GroundingValidationError


def test_schema_smart_features_validation():
    """Verify schema acceptance of 4 execution flows, lifecycle sequenceDiagram, glossary, and QA track."""
    payload_data = {
        "summary": "Engineering Intelligence platform analyzing repositories, pull requests, and architecture.",
        "architecture_pattern": "Modular Monolith",
        "subsystems": [
            {
                "name": "API Service",
                "path": "backend/app",
                "purpose": "Exposes REST endpoints",
                "key_files": ["backend/app/main.py"],
            }
        ],
        "request_flow": [
            {
                "step_number": 1,
                "layer": "Routing",
                "file": "backend/app/main.py",
                "symbol": "app",
                "description": "Dispatches request to router",
            },
            {
                "step_number": 2,
                "layer": "Database",
                "file": "backend/app/db.py",
                "symbol": "get_db",
                "description": "Provides database session",
            },
        ],
        "application_flows": {
            "startup": [
                {
                    "step_number": 1,
                    "layer": "Bootstrap",
                    "file": "backend/app/main.py",
                    "symbol": "lifespan",
                    "description": "Initializes app state and configurations",
                }
            ],
            "api_lifecycle": [
                {
                    "step_number": 1,
                    "layer": "Routing",
                    "file": "backend/app/main.py",
                    "symbol": "app",
                    "description": "Routes incoming HTTP requests",
                }
            ],
            "auth_flow": [
                {
                    "step_number": 1,
                    "layer": "Auth Middleware",
                    "file": "backend/app/auth/dependencies.py",
                    "symbol": "get_current_user",
                    "description": "Decodes JWT bearer token and enforces RBAC",
                }
            ],
            "db_flow": [
                {
                    "step_number": 1,
                    "layer": "Connection Pool",
                    "file": "backend/app/db.py",
                    "symbol": "engine",
                    "description": "Acquires connection from SQLAlchemy pool",
                }
            ],
        },
        "lifecycle_diagram": (
            "sequenceDiagram\n"
            "    autonumber\n"
            "    actor User\n"
            "    participant API as FastAPI Router\n"
            "    participant Auth as Auth Middleware\n"
            "    participant DB as Postgres DB\n"
            "    User->>API: GET /api/v1/repositories\n"
            "    API->>Auth: Verify JWT\n"
            "    Auth-->>API: Authorized\n"
            "    API->>DB: Query repositories\n"
            "    DB-->>API: Records\n"
            "    API-->>User: 200 OK JSON"
        ),
        "tracks": {
            "backend": {
                "track_name": "backend",
                "reading_order": [
                    {
                        "file_path": "backend/app/main.py",
                        "role": "Entrypoint",
                        "why_read": "Server bootstrap and middleware setup",
                        "focus_symbols": ["app"],
                    }
                ],
                "milestones": [
                    {
                        "id": "be_1",
                        "title": "Run Server",
                        "description": "Run local uvicorn server",
                        "action_type": "run_command",
                        "action_hint": "uvicorn backend.app.main:app",
                    }
                ],
            },
            "frontend": {
                "track_name": "frontend",
                "reading_order": [],
                "milestones": [],
            },
            "fullstack": {
                "track_name": "fullstack",
                "reading_order": [],
                "milestones": [],
            },
            "qa": {
                "track_name": "qa",
                "reading_order": [
                    {
                        "file_path": "backend/tests/test_onboarding.py",
                        "role": "Integration Test",
                        "why_read": "Validates onboarding API contracts and access control",
                        "focus_symbols": ["test_blueprint_retrieval"],
                        "responsibilities": "Verifies RBAC rules and payload schema",
                        "important_functions": ["test_blueprint_retrieval"],
                        "dependencies": ["pytest", "fastapi"],
                        "relevant_documentation": "docs/testing_guide.md",
                    }
                ],
                "milestones": [
                    {
                        "id": "qa_1",
                        "title": "Run Pytest Suite",
                        "description": "Execute pytest with coverage",
                        "action_type": "run_command",
                        "action_hint": "pytest backend/tests/ -v",
                        "practical_task": "Execute full test suite and inspect schema validation logs",
                    }
                ],
            },
        },
        "glossary": [
            {
                "term": "RepositoryBlueprint",
                "category": "domain",
                "definition": "Database model holding cached architectural intelligence and learning tracks",
                "related_files": ["backend/app/onboarding/models.py"],
            },
            {
                "term": "VectorSearch",
                "category": "architecture",
                "definition": "pgvector semantic similarity search over repository chunks",
                "related_files": ["backend/app/rag/service.py"],
            },
        ],
        "caution_zones": [
            {
                "path": "backend/app/auth",
                "risk_level": "critical",
                "reason": "Security and token validation boundaries",
            }
        ],
        "safe_starter_areas": [
            {
                "area": "Unit Test Helpers",
                "description": "Isolated mocking fixtures and asserts",
                "starter_ideas": ["Add test cases for utility functions"],
            }
        ],
        "mermaid_diagram": "flowchart TD\n    A[Client] --> B[FastAPI]\n    B --> C[Postgres]",
    }

    payload = LLMBlueprintPayload.model_validate(payload_data)
    assert payload.architecture_pattern == "Modular Monolith"
    assert "qa" in payload.tracks
    assert len(payload.tracks["qa"].reading_order) == 1
    assert payload.tracks["qa"].reading_order[0].responsibilities == "Verifies RBAC rules and payload schema"
    assert payload.application_flows is not None
    assert len(payload.application_flows.startup) == 1
    assert len(payload.application_flows.auth_flow) == 1
    assert payload.lifecycle_diagram.startswith("sequenceDiagram")
    assert len(payload.glossary) == 2
    assert payload.glossary[0].term == "RepositoryBlueprint"


def test_grounding_filters_and_validates_smart_features():
    """Verify that execution flow and glossary files are grounded against indexed paths."""
    indexed_paths = {
        "backend/app/main.py",
        "backend/app/db.py",
        "backend/app/auth/dependencies.py",
        "backend/app/onboarding/models.py",
    }

    payload_data = {
        "summary": "Engineering Intelligence platform analyzing repositories.",
        "architecture_pattern": "Modular Monolith",
        "subsystems": [
            {
                "name": "API Service",
                "path": "backend/app",
                "purpose": "REST API",
                "key_files": ["backend/app/main.py"],
            }
        ],
        "request_flow": [
            {
                "step_number": 1,
                "layer": "Routing",
                "file": "backend/app/main.py",
                "description": "Routing entry",
            },
            {
                "step_number": 2,
                "layer": "DB",
                "file": "backend/app/db.py",
                "description": "DB connection",
            },
        ],
        "application_flows": {
            "startup": [
                {
                    "step_number": 1,
                    "layer": "Bootstrap",
                    "file": "backend/app/main.py",
                    "description": "Boots app",
                },
                {
                    "step_number": 2,
                    "layer": "Unindexed Layer",
                    "file": "fabricated/missing/boot.py",
                    "description": "Hallucinated step",
                },
            ],
            "api_lifecycle": [],
            "auth_flow": [],
            "db_flow": [],
        },
        "lifecycle_diagram": "sequenceDiagram\n    A->>B: Call",
        "tracks": {
            "backend": {"track_name": "backend", "reading_order": [], "milestones": []},
            "frontend": {"track_name": "frontend", "reading_order": [], "milestones": []},
            "fullstack": {"track_name": "fullstack", "reading_order": [], "milestones": []},
        },
        "glossary": [
            {
                "term": "Model",
                "category": "domain",
                "definition": "ORM Model",
                "related_files": ["backend/app/onboarding/models.py", "unindexed/fabricated.py"],
            }
        ],
        "caution_zones": [],
        "safe_starter_areas": [],
        "mermaid_diagram": "flowchart TD\n    A --> B",
    }

    payload = LLMBlueprintPayload.model_validate(payload_data)

    # Instantiate OnboardingService with dummy session
    service = OnboardingService(db=None)
    service._enforce_grounding_invariants(payload, indexed_paths)

    # The unindexed step in startup flow must be dropped
    assert len(payload.application_flows.startup) == 1
    assert payload.application_flows.startup[0].file == "backend/app/main.py"

    # Fabricated related file in glossary must be filtered out
    assert payload.glossary[0].related_files == ["backend/app/onboarding/models.py"]


def test_blueprint_persistence_and_api_roundtrip(db_session: Session):
    """Test full persistence of smart onboarding fields to DB and retrieval via API."""
    now = datetime.now(timezone.utc)

    # 1. Seed org, user, membership, repo
    user = User(email="smart_dev@example.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    org = Organization(name="SmartOrg")
    db_session.add(org)
    db_session.flush()

    membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role=RoleEnum.DEVELOPER)
    db_session.add(membership)

    project = Project(name="Core Project", organization_id=org.id)
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-smart-1",
        github_name="smart-repo",
        github_owner="SmartOrg",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(repo)
    db_session.flush()

    doc = Document(repository_id=repo.id, path="backend/main.py", content_hash="hash123")
    db_session.add(doc)
    db_session.flush()

    # 2. Seed blueprint with smart features
    bp = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        status="ready",
        summary="A smart repository intelligence platform.",
        architecture_pattern="Modular Monolith",
        subsystems=[{"name": "Core", "path": "backend", "purpose": "Core app", "key_files": ["backend/main.py"]}],
        request_flow=[
            {"step_number": 1, "layer": "API", "file": "backend/main.py", "symbol": "api", "description": "Request dispatch"},
            {"step_number": 2, "layer": "DB", "file": "backend/db.py", "symbol": "db", "description": "DB query"},
        ],
        tracks={
            "backend": {"track_name": "backend", "reading_order": [], "milestones": []},
            "frontend": {"track_name": "frontend", "reading_order": [], "milestones": []},
            "fullstack": {"track_name": "fullstack", "reading_order": [], "milestones": []},
            "qa": {
                "track_name": "qa",
                "reading_order": [
                    {
                        "file_path": "backend/tests/test_api.py",
                        "role": "Integration Suite",
                        "why_read": "Understand test setup and mocks",
                        "focus_symbols": ["test_api_get"],
                        "responsibilities": "Verifies API responses",
                        "important_functions": ["test_api_get"],
                        "dependencies": ["pytest"],
                        "relevant_documentation": "docs/qa.md",
                    }
                ],
                "milestones": [
                    {
                        "id": "qa_m1",
                        "title": "Run QA Tests",
                        "description": "Execute pytest with coverage",
                        "action_type": "run_command",
                        "action_hint": "pytest backend/tests/ -v",
                        "practical_task": "Run tests and inspect log output",
                    }
                ],
            },
        },
        application_flows={
            "startup": [
                {"step_number": 1, "layer": "Bootstrap", "file": "backend/main.py", "symbol": "init", "description": "App init"}
            ],
            "api_lifecycle": [
                {"step_number": 1, "layer": "Routing", "file": "backend/main.py", "symbol": "router", "description": "Routing"}
            ],
            "auth_flow": [
                {"step_number": 1, "layer": "Auth", "file": "backend/auth.py", "symbol": "verify", "description": "Verify token"}
            ],
            "db_flow": [
                {"step_number": 1, "layer": "DB", "file": "backend/db.py", "symbol": "session", "description": "Session"}
            ],
        },
        lifecycle_diagram="sequenceDiagram\n    Client->>Server: Request\n    Server-->>Client: Response",
        glossary=[
            {
                "term": "SmartBlueprint",
                "category": "domain",
                "definition": "Engineered onboarding guide with execution flows",
                "related_files": ["backend/main.py"],
            }
        ],
        caution_zones=[{"path": "backend/auth.py", "risk_level": "critical", "reason": "Auth logic"}],
        safe_starter_areas=[{"area": "Docs", "description": "Safe markdown", "starter_ideas": ["Improve readme"]}],
        mermaid_diagram="flowchart TD\n    A --> B",
        generation_completed_at=now,
    )
    db_session.add(bp)
    db_session.commit()

    # 3. Test API GET /repositories/{repo.id}/onboarding/blueprint
    from backend.app.auth.dependencies import get_current_user
    from backend.app.db import get_db

    def _override_get_current_user():
        db_session.refresh(user)
        return user

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db

    try:
        client = TestClient(app)
        res = client.get(f"/repositories/{repo.id}/onboarding/blueprint")
        assert res.status_code == 200, res.text
        data = res.json()

        assert data["architecture_pattern"] == "Modular Monolith"
        assert "qa" in data["tracks"]
        assert len(data["tracks"]["qa"]["reading_order"]) == 1
        assert data["tracks"]["qa"]["reading_order"][0]["responsibilities"] == "Verifies API responses"

        # Check execution flows
        assert "application_flows" in data and data["application_flows"] is not None
        assert len(data["application_flows"]["startup"]) == 1
        assert len(data["application_flows"]["auth_flow"]) == 1

        # Check sequence diagram
        assert data["lifecycle_diagram"].startswith("sequenceDiagram")

        # Check glossary
        assert len(data["glossary"]) == 1
        assert data["glossary"][0]["term"] == "SmartBlueprint"

        # 4. Test PUT progress updating active_track to 'qa'
        progress_res = client.put(
            f"/repositories/{repo.id}/onboarding/progress",
            json={
                "active_track": "qa",
                "completed_milestones": ["qa_m1"],
                "notes": "My private test notes for QA path",
            },
        )
        assert progress_res.status_code == 200, progress_res.text
        prog_data = progress_res.json()
        assert prog_data["active_track"] == "qa"
        assert prog_data["completed_milestones"] == ["qa_m1"]
        assert prog_data["notes"] == "My private test notes for QA path"

        # 5. Verify Anti-Surveillance Privacy: Another user cannot see this user's notes
        user_b = User(email="manager@example.com", password_hash="hash")
        db_session.add(user_b)
        db_session.flush()
        membership_b = OrganizationMembership(user_id=user_b.id, organization_id=org.id, role=RoleEnum.TEAM_LEAD)
        db_session.add(membership_b)
        db_session.commit()

        # Switch authentication to user_b (Manager)
        def _override_manager_user():
            db_session.refresh(user_b)
            return user_b

        app.dependency_overrides[get_current_user] = _override_manager_user
        res_manager = client.get(f"/repositories/{repo.id}/onboarding/progress")
        assert res_manager.status_code == 200
        mgr_data = res_manager.json()

        # Manager gets their OWN clean progress record, NEVER user A's private notes or checklist
        assert mgr_data["notes"] == ""
        assert mgr_data["completed_milestones"] == []
        assert mgr_data["notes"] != "My private test notes for QA path"

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
