"""
Circular Dependency Detector — RepoMind 2.0 Architecture Engine.

Detects direct and transitive cyclic dependencies between files and packages
using graph cycle analysis algorithms.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Tuple
import networkx as nx


@dataclass
class CircularDependency:
    cycle_path: List[str]
    length: int
    participating_files: List[str]
    severity: str  # critical | high | medium
    title: str
    explanation: str
    decoupling_recommendation: str


def detect_circular_dependencies(
    import_edges: List[Tuple[str, str]],  # (source_file, target_file)
    max_cycles: int = 50,
) -> List[CircularDependency]:
    """
    Analyzes internal import edges to discover direct and transitive dependency loops.
    """
    G = nx.DiGraph()

    for src, tgt in import_edges:
        if src and tgt and src != tgt:
            G.add_edge(src, tgt)

    cycles_found: List[CircularDependency] = []
    seen_cycle_sets: Set[frozenset] = set()

    try:
        # Use simple_cycles generator
        for raw_cycle in nx.simple_cycles(G):
            if len(raw_cycle) < 2:
                continue

            cycle_set = frozenset(raw_cycle)
            if cycle_set in seen_cycle_sets:
                continue
            seen_cycle_sets.add(cycle_set)

            cycle_path = raw_cycle + [raw_cycle[0]]
            cycle_len = len(raw_cycle)

            if cycle_len == 2:
                severity = "critical"
                cycle_type_str = "Direct circular dependency"
                advice = (
                    f"Files '{raw_cycle[0]}' and '{raw_cycle[1]}' mutually import each other. "
                    "Extract shared types/constants into a third shared module or inject dependencies via function arguments."
                )
            else:
                severity = "high"
                cycle_type_str = f"Transitive circular dependency ({cycle_len} hops)"
                advice = (
                    f"Transitive cycle traversing {cycle_len} files: {' -> '.join(cycle_path)}. "
                    "Apply Dependency Inversion: define an abstract interface in a lower layer or break the loop at the weakest coupling link."
                )

            cycles_found.append(CircularDependency(
                cycle_path=cycle_path,
                length=cycle_len,
                participating_files=raw_cycle,
                severity=severity,
                title=f"{cycle_type_str}: {raw_cycle[0]} <-> {raw_cycle[1]}",
                explanation=f"Circular dependency chain detected: {' -> '.join(cycle_path)}. Cyclic imports lead to tight coupling, runtime import failures, and fragile initialization orders.",
                decoupling_recommendation=advice,
            ))

            if len(cycles_found) >= max_cycles:
                break

    except Exception:
        # Fallback to strongly connected components if graph is large
        sccs = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
        for scc in sccs[:max_cycles]:
            files = sorted(list(scc))
            cycles_found.append(CircularDependency(
                cycle_path=files + [files[0]],
                length=len(files),
                participating_files=files,
                severity="high",
                title=f"Cyclic component cluster ({len(files)} files)",
                explanation=f"Strongly connected cluster with mutually dependent imports: {', '.join(files[:4])}...",
                decoupling_recommendation="Break the cluster by introducing dependency injection or layered service interfaces.",
            ))

    return cycles_found
