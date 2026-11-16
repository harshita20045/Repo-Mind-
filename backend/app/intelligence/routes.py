from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.organizations.models import Repository, Project
from backend.app.organizations.service import verify_org_member
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    PackageDependency,
    RepositoryScanSummary,
)
from backend.app.intelligence.schemas import (
    RepositoryScanSummaryResponse,
    KnowledgeGraphResponse,
    GraphNodeSchema,
    GraphEdgeSchema,
    PackageDependencySchema,
    CodeSymbolSchema,
    IndexingTriggerResponse,
)

router = APIRouter(prefix="/repositories", tags=["repository-intelligence"])


def _get_authorized_repo(db: Session, repository_id: int, current_user: User) -> Repository:
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = db.get(Project, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_org_member(db, current_user.id, project.organization_id)
    return repo


@router.get(
    "/{repository_id}/intelligence/summary",
    response_model=RepositoryScanSummaryResponse,
    summary="Get repository scan summary, language stats, frameworks and entry points",
)
def get_repository_summary(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_authorized_repo(db, repository_id, current_user)
    summary = db.execute(
        select(RepositoryScanSummary).where(RepositoryScanSummary.repository_id == repository_id)
    ).scalar_one_or_none()

    if not summary:
        return RepositoryScanSummaryResponse(
            repository_id=repository_id,
            primary_language=None,
            languages={},
            frameworks=[],
            entry_points=[],
            stats={},
            architecture_summary="Repository has not been indexed yet. Trigger indexing to generate intelligence.",
            mermaid_diagram="flowchart TD\n    Unindexed['Repository unindexed']",
        )

    return RepositoryScanSummaryResponse(
        repository_id=repository_id,
        primary_language=summary.primary_language,
        languages=summary.languages or {},
        frameworks=summary.frameworks or [],
        entry_points=summary.entry_points or [],
        stats=summary.stats or {},
        architecture_summary=summary.architecture_summary,
        mermaid_diagram=summary.mermaid_diagram,
        scanned_commit_sha=summary.scanned_commit_sha,
        updated_at=summary.updated_at,
    )


@router.get(
    "/{repository_id}/intelligence/graph",
    response_model=KnowledgeGraphResponse,
    summary="Get repository code knowledge graph nodes and edges",
)
def get_repository_graph(
    repository_id: int,
    node_type: Optional[str] = Query(None, description="Filter by node_type (file, module, class, function, api_endpoint, db_model)"),
    search: Optional[str] = Query(None, description="Search node name or file path"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_repo(db, repository_id, current_user)

    stmt_nodes = select(CodeGraphNode).where(CodeGraphNode.repository_id == repository_id)
    if node_type:
        stmt_nodes = stmt_nodes.where(CodeGraphNode.node_type == node_type)
    if search:
        stmt_nodes = stmt_nodes.where(
            CodeGraphNode.name.ilike(f"%{search}%") | CodeGraphNode.file_path.ilike(f"%{search}%")
        )

    total_nodes = db.execute(
        select(func.count(CodeGraphNode.id)).where(CodeGraphNode.repository_id == repository_id)
    ).scalar() or 0

    nodes = list(db.execute(stmt_nodes.limit(limit)).scalars().all())
    node_ids = {n.id for n in nodes}

    # Fetch edges between returned nodes
    edges = []
    total_edges = db.execute(
        select(func.count(CodeGraphEdge.id)).where(CodeGraphEdge.repository_id == repository_id)
    ).scalar() or 0

    if node_ids:
        stmt_edges = select(CodeGraphEdge).where(
            CodeGraphEdge.repository_id == repository_id,
            CodeGraphEdge.source_node_id.in_(node_ids),
            CodeGraphEdge.target_node_id.in_(node_ids),
        ).limit(limit * 2)
        edges = list(db.execute(stmt_edges).scalars().all())

    return KnowledgeGraphResponse(
        nodes=[
            GraphNodeSchema(
                id=n.id,
                node_key=n.node_key,
                node_type=n.node_type,
                name=n.name,
                file_path=n.file_path,
                start_line=n.start_line,
                end_line=n.end_line,
                metadata=n.metadata_json,
            )
            for n in nodes
        ],
        edges=[
            GraphEdgeSchema(
                id=e.id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                relation_type=e.relation_type,
                weight=e.weight,
                metadata=e.metadata_json,
            )
            for e in edges
        ],
        total_nodes=total_nodes,
        total_edges=total_edges,
    )


@router.get(
    "/{repository_id}/intelligence/architecture-diagram",
    summary="Get Mermaid architecture diagram string for the repository",
)
def get_architecture_diagram(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_repo(db, repository_id, current_user)
    summary = db.execute(
        select(RepositoryScanSummary).where(RepositoryScanSummary.repository_id == repository_id)
    ).scalar_one_or_none()

    diagram = (
        summary.mermaid_diagram
        if summary and summary.mermaid_diagram
        else "flowchart TD\n    Empty['Repository not indexed yet']"
    )
    return {"mermaid_diagram": diagram}


@router.get(
    "/{repository_id}/intelligence/dependencies",
    response_model=List[PackageDependencySchema],
    summary="Get list of extracted third-party package dependencies",
)
def get_repository_dependencies(
    repository_id: int,
    ecosystem: Optional[str] = Query(None, description="Filter by ecosystem (pypi, npm, cargo, go)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_repo(db, repository_id, current_user)
    stmt = select(PackageDependency).where(PackageDependency.repository_id == repository_id)
    if ecosystem:
        stmt = stmt.where(PackageDependency.ecosystem == ecosystem)

    deps = list(db.execute(stmt.order_by(PackageDependency.package_name)).scalars().all())
    return [
        PackageDependencySchema(
            ecosystem=d.ecosystem,
            package_name=d.package_name,
            version_spec=d.version_spec,
            is_dev=d.is_dev,
            file_path=d.file_path,
        )
        for d in deps
    ]


@router.get(
    "/{repository_id}/intelligence/symbols",
    response_model=List[CodeSymbolSchema],
    summary="Search indexed classes, functions, methods, API endpoints, and database models",
)
def get_repository_symbols(
    repository_id: int,
    symbol_type: Optional[str] = Query(None, description="Filter by symbol type (class, function, method, api_endpoint, db_model)"),
    search: Optional[str] = Query(None, description="Filter by symbol name or file path"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_authorized_repo(db, repository_id, current_user)

    stmt = select(CodeGraphNode).where(
        CodeGraphNode.repository_id == repository_id,
        CodeGraphNode.node_type.notin_(["file", "module"]),
    )
    if symbol_type:
        stmt = stmt.where(CodeGraphNode.node_type == symbol_type)
    if search:
        stmt = stmt.where(
            CodeGraphNode.name.ilike(f"%{search}%") | CodeGraphNode.file_path.ilike(f"%{search}%")
        )

    stmt = stmt.order_by(CodeGraphNode.name.asc()).offset(offset).limit(limit)
    nodes = list(db.execute(stmt).scalars().all())

    return [
        CodeSymbolSchema(
            name=n.name,
            symbol_type=n.node_type,
            file_path=n.file_path,
            start_line=n.start_line,
            end_line=n.end_line,
            signature=(n.metadata_json or {}).get("signature"),
            docstring=(n.metadata_json or {}).get("docstring"),
            parent_symbol=(n.metadata_json or {}).get("parent_symbol"),
            metadata=n.metadata_json,
        )
        for n in nodes
    ]


@router.post(
    "/{repository_id}/intelligence/index",
    response_model=IndexingTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger repository intelligence indexing",
)
def trigger_intelligence_indexing(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_authorized_repo(db, repository_id, current_user)
    if repo.index_status in ("indexing",):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository indexing is already in progress.",
        )

    repo.index_status = "unindexed"
    db.commit()

    # Query existing summary counts
    summary = db.execute(
        select(RepositoryScanSummary).where(RepositoryScanSummary.repository_id == repository_id)
    ).scalar_one_or_none()

    stats = summary.stats if summary and summary.stats else {}

    return IndexingTriggerResponse(
        message=f"Repository {repo.github_owner}/{repo.github_name} queued for intelligence indexing.",
        repository_id=repository_id,
        status="unindexed",
        scanned_files_count=stats.get("total_files", 0),
        symbols_extracted_count=stats.get("nodes_count", 0),
        dependencies_count=stats.get("dependencies_count", 0),
    )
