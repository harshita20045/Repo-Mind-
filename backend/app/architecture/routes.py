"""
Architecture Intelligence Engine API Routes — RepoMind 2.0.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, RoleEnum, OrganizationMembership
from backend.app.organizations.models import Repository, Project
from backend.app.organizations.service import verify_org_member
from backend.app.architecture.models import (
    ArchitectureRule,
    ArchitectureAnalysis,
    ArchitectureViolation,
)
from backend.app.architecture.schemas import (
    ArchitectureRuleCreateRequest,
    ArchitectureRuleUpdateRequest,
    ArchitectureRuleResponse,
    ArchitectureViolationResponse,
    ArchitectureAnalysisResponse,
    CircularDependencyResponse,
    FlowChainResponse,
)
from backend.app.architecture.engine import (
    run_architecture_analysis,
    ensure_baseline_architecture_rules,
)
from backend.app.architecture.patterns import detect_architecture_pattern
from backend.app.architecture.circular import detect_circular_dependencies
from backend.app.architecture.flows import trace_architecture_flows
from backend.app.architecture.layers import classify_layer
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge

router = APIRouter(prefix="", tags=["architecture-intelligence"])


def _get_authorized_repo(db: Session, repository_id: int, current_user: User) -> tuple:
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = db.get(Project, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_org_member(db, current_user.id, project.organization_id)
    return repo, project


def _verify_rule_admin(db: Session, user_id: int, organization_id: int):
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or access denied",
        )
    role_str = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    if role_str not in (RoleEnum.ORG_ADMIN.value, RoleEnum.TEAM_LEAD.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Organization Admins or Team Leads can configure architecture rules.",
        )
    return membership


# ===========================================================================
# 1. Architecture Analysis Endpoints
# ===========================================================================

@router.get(
    "/repositories/{repository_id}/architecture/analysis",
    response_model=ArchitectureAnalysisResponse,
    summary="Get latest architecture audit and health score",
)
def get_latest_architecture_analysis(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves the latest Architecture Analysis snapshot for a repository."""
    repo, _ = _get_authorized_repo(db, repository_id, current_user)

    analysis = (
        db.query(ArchitectureAnalysis)
        .filter(ArchitectureAnalysis.repository_id == repository_id)
        .order_by(ArchitectureAnalysis.id.desc())
        .first()
    )

    if not analysis:
        # Trigger an initial audit on-the-fly
        analysis = run_architecture_analysis(db=db, repository_id=repository_id)

    return analysis


@router.post(
    "/repositories/{repository_id}/architecture/analyze",
    response_model=ArchitectureAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a fresh architecture audit",
)
def trigger_architecture_analysis(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Triggers an on-demand architectural design audit and compliance check."""
    repo, _ = _get_authorized_repo(db, repository_id, current_user)
    analysis = run_architecture_analysis(db=db, repository_id=repository_id)
    return analysis


# ===========================================================================
# 2. Rule Management Endpoints
# ===========================================================================

@router.get(
    "/repositories/{repository_id}/architecture/rules",
    response_model=List[ArchitectureRuleResponse],
    summary="List all active and configured architecture rules",
)
def list_architecture_rules(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all system-inferred and custom architecture rules for the repository."""
    _get_authorized_repo(db, repository_id, current_user)

    rules = (
        db.query(ArchitectureRule)
        .filter(ArchitectureRule.repository_id == repository_id)
        .order_by(ArchitectureRule.rule_code.asc())
        .all()
    )

    if not rules:
        # Seed baseline rules
        nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
        file_paths = [n.file_path for n in nodes if n.file_path]
        inferred = detect_architecture_pattern(file_paths)
        rules = ensure_baseline_architecture_rules(db, repository_id, inferred)

    return rules


@router.post(
    "/repositories/{repository_id}/architecture/rules",
    response_model=ArchitectureRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom architecture rule",
)
def create_architecture_rule(
    repository_id: int,
    payload: ArchitectureRuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows authorized users to define a custom architecture rule."""
    repo, project = _get_authorized_repo(db, repository_id, current_user)
    _verify_rule_admin(db, current_user.id, project.organization_id)

    # Check rule code uniqueness per repo
    existing = (
        db.query(ArchitectureRule)
        .filter(
            ArchitectureRule.repository_id == repository_id,
            ArchitectureRule.rule_code == payload.rule_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rule with code '{payload.rule_code}' already exists for this repository.",
        )

    rule = ArchitectureRule(
        repository_id=repository_id,
        rule_code=payload.rule_code,
        name=payload.name,
        description=payload.description,
        rule_type=payload.rule_type,
        source_layer=payload.source_layer,
        target_layer=payload.target_layer,
        source_pattern=payload.source_pattern,
        target_pattern=payload.target_pattern,
        severity=payload.severity or "high",
        suggested_fix=payload.suggested_fix,
        is_enabled=payload.is_enabled,
        is_system_inferred=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put(
    "/repositories/{repository_id}/architecture/rules/{rule_id}",
    response_model=ArchitectureRuleResponse,
    summary="Update or toggle an architecture rule",
)
@router.patch(
    "/repositories/{repository_id}/architecture/rules/{rule_id}",
    response_model=ArchitectureRuleResponse,
    summary="Patch or toggle an architecture rule",
)
def update_architecture_rule(
    repository_id: int,
    rule_id: int,
    payload: ArchitectureRuleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allows authorized users to edit rule boundaries, severity, or toggle is_enabled."""
    repo, project = _get_authorized_repo(db, repository_id, current_user)
    _verify_rule_admin(db, current_user.id, project.organization_id)

    rule = db.get(ArchitectureRule, rule_id)
    if not rule or rule.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Architecture rule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(rule, field, val)

    rule.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete(
    "/repositories/{repository_id}/architecture/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom architecture rule",
)
def delete_architecture_rule(
    repository_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes a custom architecture rule."""
    repo, project = _get_authorized_repo(db, repository_id, current_user)
    _verify_rule_admin(db, current_user.id, project.organization_id)

    rule = db.get(ArchitectureRule, rule_id)
    if not rule or rule.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Architecture rule not found")

    if rule.is_system_inferred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System-inferred baseline rules cannot be deleted. Disable them instead.",
        )

    db.delete(rule)
    db.commit()
    return None


@router.post(
    "/repositories/{repository_id}/architecture/rules/reset-defaults",
    response_model=List[ArchitectureRuleResponse],
    summary="Reset architecture rules to inferred pattern defaults",
)
def reset_architecture_rules_defaults(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes existing rules and re-seeds pattern-recommended baseline rules."""
    repo, project = _get_authorized_repo(db, repository_id, current_user)
    _verify_rule_admin(db, current_user.id, project.organization_id)

    # Delete existing rules
    db.query(ArchitectureRule).filter(ArchitectureRule.repository_id == repository_id).delete()
    db.commit()

    nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
    file_paths = [n.file_path for n in nodes if n.file_path]
    inferred = detect_architecture_pattern(file_paths)
    new_rules = ensure_baseline_architecture_rules(db, repository_id, inferred)
    return new_rules


# ===========================================================================
# 3. Circular Dependencies & Flows Inspection Endpoints
# ===========================================================================

@router.get(
    "/repositories/{repository_id}/architecture/circular",
    response_model=List[CircularDependencyResponse],
    summary="List circular dependency cycles detected in repository",
)
def get_circular_dependencies(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all detected circular dependency cycles across modules."""
    _get_authorized_repo(db, repository_id, current_user)

    nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
    edges = db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repository_id).all()
    node_id_map = {n.id: n for n in nodes}

    import_edges = []
    for e in edges:
        src = node_id_map.get(e.source_node_id)
        tgt = node_id_map.get(e.target_node_id)
        if src and tgt and src.file_path and tgt.file_path:
            if (e.relation_type or "imports") in ("imports", "depends_on"):
                import_edges.append((src.file_path, tgt.file_path))

    circular_deps = detect_circular_dependencies(import_edges)
    return [
        CircularDependencyResponse(
            cycle_path=c.cycle_path,
            length=c.length,
            participating_files=c.participating_files,
            severity=c.severity,
            title=c.title,
            explanation=c.explanation,
            decoupling_recommendation=c.decoupling_recommendation,
        )
        for c in circular_deps
    ]


@router.get(
    "/repositories/{repository_id}/architecture/flows",
    response_model=List[FlowChainResponse],
    summary="List API-to-Service-to-Database execution flow chains",
)
def get_architecture_flows(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves execution flow chains and flags leaky abstractions."""
    _get_authorized_repo(db, repository_id, current_user)

    nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
    edges = db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repository_id).all()
    node_id_map = {n.id: n for n in nodes}

    api_routes = []
    service_files = []
    db_model_files = []
    call_edges = []
    db_interactions = []

    for n in nodes:
        fp = n.file_path or ""
        layer = classify_layer(fp)
        if layer == "presentation" or n.node_type == "api_endpoint":
            api_routes.append({"file_path": fp, "path": n.name, "method": "ENDPOINT"})
        elif layer == "business_logic":
            service_files.append(fp)
        elif layer == "data_access" or n.node_type == "db_model":
            db_model_files.append(fp)

    for e in edges:
        src = node_id_map.get(e.source_node_id)
        tgt = node_id_map.get(e.target_node_id)
        if src and tgt and src.file_path and tgt.file_path:
            rel = e.relation_type or "calls"
            if rel == "calls":
                call_edges.append({
                    "caller_file": src.file_path,
                    "caller_name": src.name,
                    "callee_file": tgt.file_path,
                    "callee_name": tgt.name,
                    "line": src.start_line,
                })
            elif rel in ("interacts_with", "queries"):
                db_interactions.append({
                    "file_path": src.file_path,
                    "model_name": tgt.name,
                    "operation": "query",
                    "line": src.start_line,
                })

    flow_results = trace_architecture_flows(
        api_routes=api_routes,
        service_files=service_files,
        db_model_files=db_model_files,
        call_edges=call_edges,
        db_interactions=db_interactions,
    )

    all_flows = flow_results.clean_flows + flow_results.leaky_flows
    return [
        FlowChainResponse(
            endpoint_name=f.endpoint_name,
            endpoint_path=f.endpoint_path,
            route_file=f.route_file,
            service_name=f.service_name,
            service_file=f.service_file,
            model_name=f.model_name,
            model_file=f.model_file,
            is_leaky=f.is_leaky,
            evidence=f.evidence,
            suggested_fix=f.suggested_fix,
        )
        for f in all_flows
    ]
