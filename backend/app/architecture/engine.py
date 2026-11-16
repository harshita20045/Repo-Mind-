"""
Architecture Intelligence Engine Orchestrator — RepoMind 2.0.

Coordinates pattern inference, layer classification, circular dependency detection,
flow tracing, rule evaluation, health scoring, Mermaid serialization, and database persistence.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from datetime import datetime, timezone

from backend.app.architecture.models import (
    ArchitectureRule,
    ArchitectureAnalysis,
    ArchitectureViolation,
)
from backend.app.architecture.patterns import detect_architecture_pattern, InferredPatternResult
from backend.app.architecture.layers import classify_layer
from backend.app.architecture.circular import detect_circular_dependencies, CircularDependency
from backend.app.architecture.flows import trace_architecture_flows, FlowAnalysisResult
from backend.app.architecture.checker import check_architecture_rules, GroundedViolation
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge, RepositoryScanSummary
from backend.app.intelligence.scanner import RepositoryScanner
from backend.app.intelligence.parser import LanguageAwareParser

logger = logging.getLogger(__name__)


def ensure_baseline_architecture_rules(db: Session, repository_id: int, inferred: InferredPatternResult) -> List[ArchitectureRule]:
    """
    Ensures baseline architectural rules are stored in the database for this repository.
    If none exist, seeds the recommended baseline rules.
    """
    existing_rules = db.query(ArchitectureRule).filter(ArchitectureRule.repository_id == repository_id).all()
    if existing_rules:
        return existing_rules

    new_rules = []
    for r in inferred.suggested_rules:
        rule_obj = ArchitectureRule(
            repository_id=repository_id,
            rule_code=r["rule_code"],
            name=r["name"],
            description=r.get("description"),
            rule_type=r["rule_type"],
            source_layer=r.get("source_layer"),
            target_layer=r.get("target_layer"),
            source_pattern=r.get("source_pattern"),
            target_pattern=r.get("target_pattern"),
            severity=r.get("severity", "high"),
            suggested_fix=r.get("suggested_fix"),
            is_enabled=r.get("is_enabled", True),
            is_system_inferred=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        new_rules.append(rule_obj)

    db.add_all(new_rules)
    db.commit()
    for r in new_rules:
        db.refresh(r)
    return new_rules


def calculate_architecture_health_score(
    violations: List[GroundedViolation],
    circular_dependencies: List[CircularDependency],
    flow_results: FlowAnalysisResult,
) -> int:
    """
    Computes an explainable architectural health score (0 - 100).
    Penalizes based on violation severity, cyclic coupling, and leaky abstraction flows.
    """
    score = 100

    # Severity penalties
    crit_count = sum(1 for v in violations if v.severity == "critical")
    high_count = sum(1 for v in violations if v.severity == "high")
    med_count = sum(1 for v in violations if v.severity in ("medium", "low"))

    crit_penalty = min(45, crit_count * 15)
    high_penalty = min(30, high_count * 8)
    med_penalty = min(15, med_count * 3)

    # Circular dependency penalty
    cycle_penalty = min(25, len(circular_dependencies) * 10)

    # Leaky flows penalty
    leaky_penalty = min(20, len(flow_results.leaky_flows) * 5)

    total_deduction = crit_penalty + high_penalty + med_penalty + cycle_penalty + leaky_penalty
    score = max(10, min(100, 100 - total_deduction))
    return int(score)


def generate_architecture_mermaid(
    pattern: str,
    layer_summary: Dict[str, Any],
    violations: List[GroundedViolation],
    circular_dependencies: List[CircularDependency],
) -> str:
    """
    Builds a clean Mermaid diagram illustrating architectural layer topology
    with violation callouts rendered in styled red dashed links.
    """
    lines = [
        "flowchart TD",
        "    classDef layerBox fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;",
        "    classDef violationLink stroke:#ef4444,stroke-width:2px,stroke-dasharray: 5 5,color:#ef4444;",
        "    classDef cleanLink stroke:#10b981,stroke-width:2px,color:#10b981;",
    ]

    # Subgraphs for standard layers
    subgraphs = [
        ("Presentation", "Presentation / API Layer", ["routes", "controllers", "endpoints"]),
        ("BusinessLogic", "Business Logic / Services", ["services", "managers", "usecases"]),
        ("Domain", "Domain & Core Entities", ["domain", "entities", "rules"]),
        ("DataAccess", "Data Access & Persistence", ["models", "repositories", "schemas"]),
        ("Infrastructure", "Infrastructure & External Clients", ["db", "clients", "adapters"]),
    ]

    for gid, label, subitems in subgraphs:
        count = layer_summary.get(gid.lower(), {}).get("file_count", len(subitems))
        lines.append(f'    subgraph {gid}["{label} ({count} modules)"]')
        for item in subitems:
            lines.append(f'        {gid}_{item}["{item}"]:::layerBox')
        lines.append("    end")

    # Standard clean hierarchy flows
    lines.append('    Presentation_routes -->|"delegates to"| BusinessLogic_services')
    lines.append('    BusinessLogic_services -->|"applies rules on"| Domain_domain')
    lines.append('    BusinessLogic_services -->|"queries via"| DataAccess_repositories')
    lines.append('    DataAccess_repositories -->|"persists in"| Infrastructure_db')

    # Highlight violations
    for i, v in enumerate(violations[:8]):
        if v.violation_type == "api_db_isolation" or v.rule_code == "ARCH-001":
            lines.append(f'    Presentation_routes -. "VIOLATION: {v.rule_code}" .-> DataAccess_models')
            break

    for i, c in enumerate(circular_dependencies[:3]):
        lines.append(f'    BusinessLogic_services <-. "CYCLE: loop detected" .-> Domain_domain')
        break

    return "\n".join(lines)


def run_architecture_analysis(
    db: Session,
    repository_id: int,
    pull_request_id: Optional[int] = None,
    file_contents: Optional[Dict[str, str]] = None,
) -> ArchitectureAnalysis:
    """
    Executes a comprehensive architecture analysis on a repository or PR context
    and persists the snapshot in PostgreSQL.
    """
    # 1. Fetch Code Knowledge Graph Nodes and Edges
    nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
    edges = db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repository_id).all()
    scan_summary = db.query(RepositoryScanSummary).filter(RepositoryScanSummary.repository_id == repository_id).first()

    file_paths: List[str] = [n.file_path for n in nodes if n.file_path]
    frameworks: List[str] = scan_summary.frameworks if scan_summary and scan_summary.frameworks else []

    # If no graph nodes stored yet, scan file contents directly
    if not file_paths and file_contents:
        file_paths = list(file_contents.keys())

    # 2. Infer Architectural Pattern
    inferred = detect_architecture_pattern(
        file_paths=file_paths,
        frameworks=frameworks,
    )

    # 3. Ensure baseline rules exist in database
    rules = ensure_baseline_architecture_rules(db, repository_id, inferred)
    rules_dict = [
        {
            "id": r.id,
            "rule_code": r.rule_code,
            "name": r.name,
            "description": r.description,
            "rule_type": r.rule_type,
            "source_layer": r.source_layer,
            "target_layer": r.target_layer,
            "source_pattern": r.source_pattern,
            "target_pattern": r.target_pattern,
            "severity": r.severity,
            "suggested_fix": r.suggested_fix,
            "is_enabled": r.is_enabled,
        }
        for r in rules
    ]

    # 4. Extract Import Records and Dependencies
    node_id_map = {n.id: n for n in nodes}
    import_edges = []
    import_records = []
    call_edges = []
    db_interactions = []
    api_routes = []
    service_files = set()
    db_model_files = set()

    for n in nodes:
        fp = n.file_path
        if not fp:
            continue
        layer = classify_layer(fp)
        if layer == "presentation" or n.node_type == "api_endpoint":
            api_routes.append({"file_path": fp, "path": n.name, "method": "ROUTE"})
        elif layer == "business_logic":
            service_files.add(fp)
        elif layer == "data_access" or n.node_type == "db_model":
            db_model_files.add(fp)

    for e in edges:
        src_node = node_id_map.get(e.source_node_id)
        tgt_node = node_id_map.get(e.target_node_id)
        if src_node and tgt_node and src_node.file_path and tgt_node.file_path:
            src_f = src_node.file_path
            tgt_f = tgt_node.file_path
            rel = e.relation_type or "imports"

            if rel in ("imports", "depends_on"):
                import_edges.append((src_f, tgt_f))
                import_records.append({
                    "source_file": src_f,
                    "target_file": tgt_f,
                    "line": src_node.start_line or 1,
                    "raw_statement": f"from {tgt_f} import {tgt_node.name}",
                })
            elif rel in ("calls",):
                call_edges.append({
                    "caller_file": src_f,
                    "caller_name": src_node.name,
                    "callee_file": tgt_f,
                    "callee_name": tgt_node.name,
                    "line": src_node.start_line,
                })
            elif rel in ("interacts_with", "queries"):
                db_interactions.append({
                    "file_path": src_f,
                    "model_name": tgt_node.name,
                    "operation": "query",
                    "line": src_node.start_line,
                })

    # If file_contents are passed directly (e.g. in tests or PR checks), parse in-memory
    if file_contents:
        parser = LanguageAwareParser()
        for fpath, fcontent in file_contents.items():
            parsed = parser.parse_file(fpath, fcontent)
            for imp in parsed.imports:
                mod = imp.get("module", "")
                import_edges.append((fpath, mod))
                import_records.append({
                    "source_file": fpath,
                    "target_file": mod,
                    "line": imp.get("line", 1),
                    "raw_statement": f"import {mod}",
                })
            for call in parsed.calls:
                call_edges.append({
                    "caller_file": fpath,
                    "caller_name": call.get("caller", ""),
                    "callee_file": fpath,
                    "callee_name": call.get("callee", ""),
                    "line": call.get("line"),
                })
            for dbi in parsed.db_interactions:
                db_interactions.append({
                    "file_path": fpath,
                    "model_name": dbi.get("model_name", "DatabaseModel"),
                    "operation": dbi.get("operation", "query"),
                    "line": dbi.get("line"),
                })
            for api in parsed.api_definitions:
                api_routes.append({
                    "file_path": fpath,
                    "path": api.get("path", "/"),
                    "method": api.get("method", "GET"),
                })

    # 5. Circular Dependency Detection
    circular_deps = detect_circular_dependencies(import_edges)

    # 6. Flow Analysis (API -> Service -> DB)
    flow_results = trace_architecture_flows(
        api_routes=api_routes,
        service_files=list(service_files),
        db_model_files=list(db_model_files),
        call_edges=call_edges,
        db_interactions=db_interactions,
    )

    # 7. Rule Evaluation & Violations
    violations = check_architecture_rules(
        active_rules=rules_dict,
        import_records=import_records,
        circular_dependencies=circular_deps,
        flow_results=flow_results,
    )

    # 8. Layer Summary Breakdown
    layer_summary: Dict[str, Dict[str, Any]] = {}
    for fp in file_paths:
        ly = classify_layer(fp)
        layer_summary.setdefault(ly, {"file_count": 0, "files": []})
        layer_summary[ly]["file_count"] += 1
        if len(layer_summary[ly]["files"]) < 10:
            layer_summary[ly]["files"].append(fp)

    # 9. Health Score Calculation
    health_score = calculate_architecture_health_score(
        violations=violations,
        circular_dependencies=circular_deps,
        flow_results=flow_results,
    )

    # 10. Mermaid Diagram Serialization
    mermaid_diagram = generate_architecture_mermaid(
        pattern=inferred.pattern,
        layer_summary=layer_summary,
        violations=violations,
        circular_dependencies=circular_deps,
    )

    # 11. Database Persistence
    analysis = ArchitectureAnalysis(
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        health_score=health_score,
        inferred_pattern=inferred.pattern,
        pattern_confidence=inferred.confidence,
        total_violations=len(violations),
        critical_violations=sum(1 for v in violations if v.severity == "critical"),
        circular_dependency_count=len(circular_deps),
        layer_summary=layer_summary,
        flow_summary=flow_results.flow_summary,
        mermaid_diagram=mermaid_diagram,
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.flush()

    # Persist violations
    violation_objs = []
    for v in violations:
        violation_objs.append(ArchitectureViolation(
            analysis_id=analysis.id,
            rule_id=v.rule_id,
            rule_code=v.rule_code,
            violation_type=v.violation_type,
            severity=v.severity,
            title=v.title,
            explanation=v.explanation,
            suggested_correction=v.suggested_correction,
            source_file=v.source_file,
            source_line=v.source_line,
            target_file=v.target_file,
            target_line=v.target_line,
            evidence=v.evidence,
            created_at=datetime.now(timezone.utc),
        ))

    db.add_all(violation_objs)
    db.commit()
    db.refresh(analysis)

    return analysis
