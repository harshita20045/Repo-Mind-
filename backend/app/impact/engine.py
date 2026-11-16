"""
Change Impact & Blast Radius Engine — RepoMind 2.0.

Orchestrates:
  Step 1: Fine-grained change detection
  Step 2: Knowledge graph reverse dependency traversal
  Step 3: Multi-tier impact classification
  Step 4: Breaking change detection
  Step 5: Impact report assembly
  Step 6: Interactive graph visualization (JSON & Mermaid)
  Step 7: Targeted test recommendations
  Persistence: Saves to change_impact_analysis in PostgreSQL
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.impact.models import ChangeImpactAnalysis
from backend.app.impact.detector import detect_code_changes, DetectedCodeChanges
from backend.app.impact.breaking import detect_breaking_changes, BreakingChange
from backend.app.impact.traversal import traverse_dependencies, TraversalResult, AffectedComponent

logger = logging.getLogger(__name__)


def generate_test_recommendations(
    affected_components: List[AffectedComponent],
    changed_files: List[str],
) -> List[Dict[str, Any]]:
    """
    Generate prioritized test recommendations based on affected components.
    Prioritizes direct unit tests first, followed by integration tests and regression tests.
    """
    recommendations = []
    seen_tests = set()

    for comp in affected_components:
        path = comp.file_path
        if "test" in path.lower() or not path:
            continue

        basename = path.split("/")[-1]
        for ext in [".py", ".ts", ".js", ".tsx", ".jsx"]:
            if basename.endswith(ext):
                raw_name = basename[:-len(ext)]
                candidate_tests = [
                    f"test_{raw_name}{ext}",
                    f"{raw_name}.test{ext}",
                    f"{raw_name}_test{ext}",
                    f"{raw_name}.spec{ext}",
                ]

                # Determine test suite type and priority based on impact tier
                if comp.impact_tier == "directly_affected":
                    priority = "P1_HIGH"
                    test_type = "unit_test"
                    reason = f"Directly modified component: verify internal logic of '{comp.name}'."
                elif comp.impact_tier == "indirectly_affected":
                    priority = "P2_MEDIUM"
                    test_type = "integration_test"
                    reason = f"Direct dependency changed: verify interface contract between '{comp.name}' and modified symbols."
                else:
                    priority = "P3_LOW"
                    test_type = "regression_test"
                    reason = f"Shared subsystem component: execute regression check."

                for t_name in candidate_tests[:2]:
                    if t_name not in seen_tests:
                        seen_tests.add(t_name)
                        recommendations.append({
                            "target_component": comp.name,
                            "target_file": path,
                            "recommended_test_file": t_name,
                            "test_type": test_type,
                            "priority": priority,
                            "reason": reason,
                            "command": f"pytest backend/tests/{t_name}" if ext == ".py" else f"npm test -- {t_name}",
                        })
                break

    # Flag untested gaps: directly affected components with no test file changed in the PR
    test_files_in_pr = [f for f in changed_files if "test" in f.lower()]
    if not test_files_in_pr and affected_components:
        recommendations.insert(0, {
            "target_component": "PR Test Coverage Gap",
            "target_file": changed_files[0] if changed_files else "",
            "recommended_test_file": "Missing Tests",
            "test_type": "coverage_gap",
            "priority": "P0_CRITICAL",
            "reason": "This PR touches source files without adding or updating corresponding test files.",
            "command": "pytest backend/tests/ or npm test",
        })

    return recommendations[:15]


def generate_impact_mermaid(
    subgraph_nodes: List[Dict[str, Any]],
    subgraph_edges: List[Dict[str, Any]],
) -> str:
    """
    Serialize affected subgraph into a clear Mermaid flowchart diagram.
    Uses color-coded node styles for changed, direct, indirect, and breaking components.
    """
    if not subgraph_nodes:
        return "flowchart LR\n    NoChanges[\"No significant affected components detected\"]"

    lines = [
        "flowchart LR",
        "    classDef changed fill:#2563eb,stroke:#1d4ed8,stroke-width:2px,color:#fff;",
        "    classDef direct fill:#d97706,stroke:#b45309,stroke-width:2px,color:#fff;",
        "    classDef indirect fill:#475569,stroke:#334155,stroke-width:1px,color:#fff;",
        "    classDef breaking fill:#dc2626,stroke:#b91c1c,stroke-width:2px,color:#fff;",
    ]

    node_id_map = {}
    for i, n in enumerate(subgraph_nodes[:25]):
        nid = f"N{i+1}"
        node_id_map[n["id"]] = nid
        label = n.get("label", n["id"])
        tier = n.get("impact_tier", "indirectly_affected")

        # Sanitize label
        clean_label = label.replace('"', '').replace("'", "")[:28]
        lines.append(f'    {nid}["{clean_label}"]')

        if tier == "directly_affected":
            if n.get("distance", 1) == 0:
                lines.append(f'    class {nid} changed;')
            else:
                lines.append(f'    class {nid} direct;')
        else:
            lines.append(f'    class {nid} indirect;')

    for e in subgraph_edges[:35]:
        src = e["source"]
        tgt = e["target"]
        if src in node_id_map and tgt in node_id_map and src != tgt:
            rel = e.get("relation_type", "impacts")
            lines.append(f'    {node_id_map[src]} -->|"{rel}"| {node_id_map[tgt]}')

    return "\n".join(lines)


def run_change_impact_analysis(
    db: Session,
    repository_id: int,
    diff: str,
    pull_request_id: Optional[int] = None,
    review_run_id: Optional[int] = None,
    commit_sha: Optional[str] = None,
    target_branch: str = "main",
    old_file_contents: Optional[Dict[str, str]] = None,
    new_file_contents: Optional[Dict[str, str]] = None,
    max_depth: int = 3,
) -> ChangeImpactAnalysis:
    """
    Execute full change impact and blast radius analysis and persist to database.
    """
    logger.info("Starting Change Impact Analysis for repo %d (PR: %s)", repository_id, pull_request_id)

    # 1. Fine-Grained Change Detection
    changes: DetectedCodeChanges = detect_code_changes(
        diff=diff,
        file_contents=new_file_contents or {},
    )

    # 2. Dependency Traversal & Classification
    traversal: TraversalResult = traverse_dependencies(
        db=db,
        repository_id=repository_id,
        changes=changes,
        max_depth=max_depth,
    )

    # 3. Breaking Change Detection
    breaking_changes: List[BreakingChange] = detect_breaking_changes(
        diff=diff,
        changes=changes,
        old_file_contents=old_file_contents,
        new_file_contents=new_file_contents,
    )

    # 4. Test Recommendations
    test_recs = generate_test_recommendations(
        affected_components=traversal.affected_components,
        changed_files=changes.changed_files,
    )

    # 5. Graph Visualization Data
    mermaid_diagram = generate_impact_mermaid(
        subgraph_nodes=traversal.subgraph_nodes,
        subgraph_edges=traversal.subgraph_edges,
    )

    graph_viz_payload = {
        "nodes": traversal.subgraph_nodes,
        "edges": traversal.subgraph_edges,
        "mermaid": mermaid_diagram,
    }

    # 6. Overall Risk Level
    breaking_count = len(breaking_changes)
    direct_count = traversal.directly_affected_count
    indirect_count = traversal.indirectly_affected_count

    if breaking_count > 0 or direct_count > 15:
        risk_level = "critical"
    elif direct_count > 5 or indirect_count > 10:
        risk_level = "high"
    elif direct_count > 0 or indirect_count > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Human-readable summary
    summary_parts = [
        f"Change Impact Analysis: {direct_count} directly affected component(s), {indirect_count} indirect dependent(s).",
    ]
    if breaking_count > 0:
        summary_parts.append(f"ALERT: {breaking_count} potential breaking change(s) detected.")
    else:
        summary_parts.append("Zero breaking API or signature mutations detected.")

    summary = " ".join(summary_parts)

    # Convert dataclasses to JSONB serializable dictionaries
    affected_components_json = [
        {
            "name": c.name,
            "file_path": c.file_path,
            "component_type": c.component_type,
            "impact_tier": c.impact_tier,
            "relationship": c.relationship,
            "why_affected": c.why_affected,
            "severity": c.severity,
            "distance": c.distance,
            "supporting_evidence": c.supporting_evidence,
            "suggested_verification": c.suggested_verification,
        }
        for c in traversal.affected_components
    ]

    breaking_changes_json = [
        {
            "change_type": b.change_type,
            "component_name": b.component_name,
            "file_path": b.file_path,
            "severity": b.severity,
            "title": b.title,
            "description": b.description,
            "evidence": b.evidence,
            "suggested_fix": b.suggested_fix,
        }
        for b in breaking_changes
    ]

    # 7. Persist to PostgreSQL
    analysis = ChangeImpactAnalysis(
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        review_run_id=review_run_id,
        commit_sha=commit_sha,
        target_branch=target_branch,
        risk_level=risk_level,
        directly_affected_count=direct_count,
        indirectly_affected_count=indirect_count,
        breaking_changes_count=breaking_count,
        affected_components=affected_components_json,
        breaking_changes=breaking_changes_json,
        test_recommendations=test_recs,
        graph_visualization=graph_viz_payload,
        summary=summary,
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info("Change Impact Analysis %d persisted successfully: risk=%s", analysis.id, risk_level)
    return analysis
