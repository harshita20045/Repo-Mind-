"""
API-to-Service-to-Database Flow Tracer — RepoMind 2.0 Architecture Engine.

Analyzes execution paths and call graphs from API endpoints through business services
down to persistent database models, detecting leaky abstractions and structural anti-patterns.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class FlowChain:
    endpoint_name: str
    endpoint_path: str
    route_file: str
    service_name: Optional[str] = None
    service_file: Optional[str] = None
    model_name: Optional[str] = None
    model_file: Optional[str] = None
    is_leaky: bool = False  # Direct route -> model access bypassing service
    evidence: str = ""
    suggested_fix: Optional[str] = None


@dataclass
class FlowAnalysisResult:
    total_flows: int
    clean_flows: List[FlowChain] = field(default_factory=list)
    leaky_flows: List[FlowChain] = field(default_factory=list)
    god_services: List[Dict[str, Any]] = field(default_factory=list)
    orphaned_models: List[str] = field(default_factory=list)
    flow_summary: Dict[str, Any] = field(default_factory=dict)


def trace_architecture_flows(
    api_routes: List[Dict[str, Any]],
    service_files: List[str],
    db_model_files: List[str],
    call_edges: List[Dict[str, Any]],  # [{caller_file, caller_name, callee_file, callee_name, line}]
    db_interactions: List[Dict[str, Any]],  # [{file_path, model_name, operation, line}]
) -> FlowAnalysisResult:
    """
    Traces API routes through call graph edges down to services and database models.
    """
    clean_flows: List[FlowChain] = []
    leaky_flows: List[FlowChain] = []

    # Map interactions by file
    interactions_by_file: Dict[str, List[Dict[str, Any]]] = {}
    for dbi in db_interactions:
        interactions_by_file.setdefault(dbi.get("file_path", ""), []).append(dbi)

    # Map calls by caller file
    calls_by_caller_file: Dict[str, List[Dict[str, Any]]] = {}
    for edge in call_edges:
        calls_by_caller_file.setdefault(edge.get("caller_file", ""), []).append(edge)

    # Check each API route
    for route in api_routes:
        route_file = route.get("file_path", "")
        route_path = route.get("path", "")
        route_method = route.get("method", "GET")
        endpoint_label = route.get("endpoint_name") or f"{route_method} {route_path}"

        # 1. Did the route file directly interact with a DB model or session?
        direct_dbis = interactions_by_file.get(route_file, [])
        if direct_dbis:
            for dbi in direct_dbis:
                model_name = dbi.get("model_name", "DatabaseModel")
                leaky_flows.append(FlowChain(
                    endpoint_name=endpoint_label,
                    endpoint_path=route_path,
                    route_file=route_file,
                    service_name=None,
                    service_file=None,
                    model_name=model_name,
                    model_file=dbi.get("file_path"),
                    is_leaky=True,
                    evidence=f"Route '{endpoint_label}' in {route_file}:{dbi.get('line', '')} directly executes DB {dbi.get('operation', 'query')} on '{model_name}'.",
                    suggested_fix=f"Move the database query for '{model_name}' into a domain service method and invoke it from the route handler.",
                ))
            continue

        # 2. Check if route delegates to a service
        outgoing_calls = calls_by_caller_file.get(route_file, [])
        service_called = None
        service_file = None

        for call in outgoing_calls:
            target_f = call.get("callee_file", "")
            if any(target_f == sf or sf in target_f for sf in service_files) or "service" in target_f.lower():
                service_called = call.get("callee_name", "ServiceMethod")
                service_file = target_f
                break

        if service_called:
            # Check if service touches a model
            service_dbis = interactions_by_file.get(service_file, []) if service_file else []
            model_name = service_dbis[0].get("model_name") if service_dbis else "PersistenceLayer"
            clean_flows.append(FlowChain(
                endpoint_name=endpoint_label,
                endpoint_path=route_path,
                route_file=route_file,
                service_name=service_called,
                service_file=service_file,
                model_name=model_name,
                is_leaky=False,
                evidence=f"Route -> {service_called} ({service_file}) -> {model_name}",
            ))
        else:
            # Standalone route
            clean_flows.append(FlowChain(
                endpoint_name=endpoint_label,
                endpoint_path=route_path,
                route_file=route_file,
                service_name=None,
                service_file=None,
                model_name=None,
                is_leaky=False,
                evidence="Standard endpoint flow",
            ))

    # Detect God Services (services referencing excessive distinct models)
    god_services = []
    service_model_counts: Dict[str, Set[str]] = {}
    for dbi in db_interactions:
        fp = dbi.get("file_path", "")
        if "service" in fp.lower() or any(fp == sf for sf in service_files):
            model = dbi.get("model_name")
            if model:
                service_model_counts.setdefault(fp, set()).add(model)

    for s_file, models in service_model_counts.items():
        if len(models) >= 8:
            god_services.append({
                "service_file": s_file,
                "model_count": len(models),
                "models": sorted(list(models)),
                "warning": f"Service touches {len(models)} distinct models, violating Single Responsibility.",
            })

    total_flows = len(clean_flows) + len(leaky_flows)
    flow_summary = {
        "total_flows": total_flows,
        "clean_flow_count": len(clean_flows),
        "leaky_flow_count": len(leaky_flows),
        "god_service_count": len(god_services),
    }

    return FlowAnalysisResult(
        total_flows=total_flows,
        clean_flows=clean_flows,
        leaky_flows=leaky_flows,
        god_services=god_services,
        orphaned_models=[],
        flow_summary=flow_summary,
    )
