"""
Dependency Traversal & Impact Classification — RepoMind 2.0 Change Impact Engine.

Traverses the Code Knowledge Graph along reverse dependency edges (incoming imports,
calls, inheritances, and API expositions) to identify:
  - Direct dependents (1 hop)
  - Transitive / indirect dependents (2..k hops)
  - Affected API consumers and endpoints
  - Database model downstream consumers

Classifies components into 4 grounded tiers:
  1. directly_affected
  2. indirectly_affected
  3. potentially_affected
  4. no_identified_impact
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session

from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.impact.detector import DetectedCodeChanges

logger = logging.getLogger(__name__)


@dataclass
class AffectedComponent:
    """Represents a component impacted by the code modifications."""
    name: str
    file_path: str
    component_type: str  # file | module | function | class | api_endpoint | db_model
    impact_tier: str     # directly_affected | indirectly_affected | potentially_affected
    relationship: str    # modified | imports | calls | inherits | exposes | transitive_dependency | shared_utility
    why_affected: str
    severity: str        # critical | high | medium | low
    distance: int = 1
    supporting_evidence: Optional[str] = None
    suggested_verification: Optional[str] = None


@dataclass
class TraversalResult:
    affected_components: List[AffectedComponent] = field(default_factory=list)
    directly_affected_count: int = 0
    indirectly_affected_count: int = 0
    potentially_affected_count: int = 0
    subgraph_nodes: List[Dict[str, Any]] = field(default_factory=list)
    subgraph_edges: List[Dict[str, Any]] = field(default_factory=list)


def traverse_dependencies(
    db: Session,
    repository_id: int,
    changes: DetectedCodeChanges,
    max_depth: int = 3,
) -> TraversalResult:
    """
    Traverse the persistent Code Knowledge Graph from modified files and symbols.
    """
    normalized_changed_files = [f.replace("\\", "/").lstrip("/") for f in changes.changed_files]

    # Fetch all graph nodes for this repository
    nodes = db.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repository_id).all()
    if not nodes:
        # Fallback if graph has not been indexed yet
        return _fallback_traversal(changes)

    node_by_id = {n.id: n for n in nodes}
    node_by_key = {n.node_key: n for n in nodes}

    # Fetch all edges
    edges = db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repository_id).all()

    # Build reverse dependency graph (G_rev)
    # If A imports/calls B, the edge in CodeGraphEdge is A -> B.
    # In G_rev, when B changes, changes flow from B -> A.
    G_rev = nx.DiGraph()

    for n in nodes:
        G_rev.add_node(
            n.id,
            node_key=n.node_key,
            node_type=n.node_type,
            name=n.name,
            file_path=n.file_path,
        )

    for e in edges:
        if e.source_node_id in node_by_id and e.target_node_id in node_by_id:
            # Reverse edge: target (callee/importee) -> source (caller/importer)
            G_rev.add_edge(
                e.target_node_id,
                e.source_node_id,
                relation_type=e.relation_type,
                weight=e.weight,
            )

    # 1. Identify Seed Nodes (directly modified nodes)
    seed_node_ids: Set[int] = set()
    changed_symbol_names = {s.symbol_name for s in changes.changed_symbols}

    for n in nodes:
        norm_path = n.file_path.replace("\\", "/").lstrip("/")
        if norm_path in normalized_changed_files:
            if n.node_type == "file":
                seed_node_ids.add(n.id)
            elif n.name in changed_symbol_names:
                seed_node_ids.add(n.id)

    affected: List[AffectedComponent] = []
    visited_ids: Set[int] = set()

    # A. Add seed components as directly_affected
    for sid in seed_node_ids:
        n = node_by_id[sid]
        visited_ids.add(sid)
        affected.append(AffectedComponent(
            name=n.name,
            file_path=n.file_path,
            component_type=n.node_type,
            impact_tier="directly_affected",
            relationship="modified",
            why_affected=f"This component was directly modified in the pull request.",
            severity="high" if n.node_type in ("api_endpoint", "db_model") else "medium",
            distance=0,
            supporting_evidence=f"Direct file modification in {n.file_path}",
            suggested_verification=f"Run unit tests covering {n.file_path}",
        ))

    # B. Traverse downstream along G_rev using BFS up to max_depth
    direct_count = len(seed_node_ids)
    indirect_count = 0
    potential_count = 0

    subgraph_edges_collected = []

    for sid in seed_node_ids:
        # BFS traversal
        queue = [(sid, 0)]
        while queue:
            curr_id, dist = queue.pop(0)
            if dist >= max_depth:
                continue

            for neighbor_id in G_rev.successors(curr_id):
                edge_data = G_rev.get_edge_data(curr_id, neighbor_id)
                rel_type = edge_data.get("relation_type", "depends_on")
                subgraph_edges_collected.append({
                    "source_id": curr_id,
                    "target_id": neighbor_id,
                    "relation_type": rel_type,
                })

                if neighbor_id not in visited_ids:
                    visited_ids.add(neighbor_id)
                    neighbor_node = node_by_id[neighbor_id]
                    curr_node = node_by_id[curr_id]

                    new_dist = dist + 1
                    if new_dist == 1:
                        tier = "directly_affected"
                        direct_count += 1
                        severity = "high" if neighbor_node.node_type == "api_endpoint" else "medium"
                    elif new_dist == 2:
                        tier = "indirectly_affected"
                        indirect_count += 1
                        severity = "medium"
                    else:
                        tier = "potentially_affected"
                        potential_count += 1
                        severity = "low"

                    affected.append(AffectedComponent(
                        name=neighbor_node.name,
                        file_path=neighbor_node.file_path,
                        component_type=neighbor_node.node_type,
                        impact_tier=tier,
                        relationship=rel_type,
                        why_affected=f"{rel_type.capitalize()} '{curr_node.name}' (distance: {new_dist} hop(s)).",
                        severity=severity,
                        distance=new_dist,
                        supporting_evidence=f"Dependency edge: {neighbor_node.file_path} -> {curr_node.file_path} ({rel_type})",
                        suggested_verification=f"Run integration test suite for {neighbor_node.file_path}",
                    ))
                    queue.append((neighbor_id, new_dist))

    # C. Add Potentially Affected (same module / shared configs)
    for n in nodes:
        if n.id not in visited_ids:
            norm_path = n.file_path.replace("\\", "/").lstrip("/")
            # Check if in same directory as a changed file
            for cf in normalized_changed_files:
                if "/" in cf and "/" in norm_path:
                    if cf.rsplit("/", 1)[0] == norm_path.rsplit("/", 1)[0]:
                        visited_ids.add(n.id)
                        potential_count += 1
                        affected.append(AffectedComponent(
                            name=n.name,
                            file_path=n.file_path,
                            component_type=n.node_type,
                            impact_tier="potentially_affected",
                            relationship="shared_utility",
                            why_affected=f"Resides in the same subsystem directory ({cf.rsplit('/', 1)[0]}).",
                            severity="low",
                            distance=max_depth + 1,
                            supporting_evidence=f"Directory locality with {cf}",
                            suggested_verification=f"Verify subsystem regression tests.",
                        ))
                        break

    # Build Visualization Subgraph
    subgraph_nodes = []
    for comp in affected[:40]:  # Cap visualization to top 40 nodes for readability
        subgraph_nodes.append({
            "id": comp.name,
            "label": comp.name,
            "file_path": comp.file_path,
            "node_type": comp.component_type,
            "impact_tier": comp.impact_tier,
            "severity": comp.severity,
            "distance": comp.distance,
        })

    subgraph_edges = []
    seen_edges = set()
    for e in subgraph_edges_collected:
        src = node_by_id[e["source_id"]].name
        tgt = node_by_id[e["target_id"]].name
        edge_key = (src, tgt)
        if edge_key not in seen_edges and src != tgt:
            seen_edges.add(edge_key)
            subgraph_edges.append({
                "source": src,
                "target": tgt,
                "relation_type": e["relation_type"],
            })

    return TraversalResult(
        affected_components=affected,
        directly_affected_count=direct_count,
        indirectly_affected_count=indirect_count,
        potentially_affected_count=potential_count,
        subgraph_nodes=subgraph_nodes,
        subgraph_edges=subgraph_edges[:50],
    )


def _fallback_traversal(changes: DetectedCodeChanges) -> TraversalResult:
    """Fallback when database graph nodes are not yet indexed."""
    affected = []
    for f in changes.changed_files:
        affected.append(AffectedComponent(
            name=f.split("/")[-1],
            file_path=f,
            component_type="file",
            impact_tier="directly_affected",
            relationship="modified",
            why_affected="Directly modified file",
            severity="medium",
            distance=0,
            supporting_evidence=f"Direct file change in {f}",
            suggested_verification=f"Run test suite for {f}",
        ))

    return TraversalResult(
        affected_components=affected,
        directly_affected_count=len(affected),
        indirectly_affected_count=0,
        potentially_affected_count=0,
        subgraph_nodes=[{"id": a.name, "label": a.name, "impact_tier": a.impact_tier} for a in affected],
        subgraph_edges=[],
    )
