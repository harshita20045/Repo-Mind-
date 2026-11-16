"""
Architecture Pattern Inference Engine — RepoMind 2.0.

Infers repository architectural design from file tree, frameworks, documentation,
and import flows without dogmatic assumptions.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re


@dataclass
class InferredPatternResult:
    pattern: str  # layered_mvc | clean_hexagonal | modular_monolith | component_based_spa | fullstack_monorepo | event_pipeline
    display_name: str
    confidence: float  # 0.0 - 1.0
    evidence: List[str] = field(default_factory=list)
    suggested_rules: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""


DEFAULT_BASELINE_RULES = [
    {
        "rule_code": "ARCH-001",
        "name": "Controllers Must Not Directly Access Database Models",
        "description": "API route handlers and controllers must interact with persistent data through service layers rather than importing or querying database models directly.",
        "rule_type": "api_db_isolation",
        "source_layer": "presentation",
        "target_layer": "data_access",
        "source_pattern": "backend/app/*/routes.py|backend/app/api/**|*controller*",
        "target_pattern": "backend/app/*/models.py|backend/app/models/**|*model*",
        "severity": "critical",
        "suggested_fix": "Encapsulate database queries in a service or repository method and invoke the service from the route handler.",
        "is_enabled": True,
        "is_system_inferred": True,
    },
    {
        "rule_code": "ARCH-002",
        "name": "Frontend Modules Must Not Import Backend Code",
        "description": "Client-side frontend components must not directly import backend server code, models, or environment secrets.",
        "rule_type": "forbidden_dependency",
        "source_layer": "frontend_ui",
        "target_layer": "backend",
        "source_pattern": "frontend/**|client/**|src/**",
        "target_pattern": "backend/**|server/**",
        "severity": "critical",
        "suggested_fix": "Communicate with the backend exclusively through HTTP REST, GraphQL, or WebSocket endpoints.",
        "is_enabled": True,
        "is_system_inferred": True,
    },
    {
        "rule_code": "ARCH-003",
        "name": "Domain Entities Must Not Depend on Infrastructure",
        "description": "Core business domain entities and rules must not import external infrastructure adapters, database drivers, or HTTP clients.",
        "rule_type": "layer_boundary",
        "source_layer": "domain",
        "target_layer": "infrastructure",
        "source_pattern": "*/domain/**|*/entities/**",
        "target_pattern": "*/infrastructure/**|*/infra/**|*/clients/**",
        "severity": "high",
        "suggested_fix": "Apply Dependency Inversion: define domain interfaces/protocols in domain and implement them in infrastructure adapters.",
        "is_enabled": True,
        "is_system_inferred": True,
    },
    {
        "rule_code": "ARCH-004",
        "name": "Shared Utilities Must Not Import Business Services",
        "description": "Cross-cutting utilities and helper libraries must remain leaf nodes and never import business logic or controllers.",
        "rule_type": "forbidden_dependency",
        "source_layer": "shared_utility",
        "target_layer": "business_logic",
        "source_pattern": "*/utils/**|*/common/**|*/helpers/**",
        "target_pattern": "*/services/**|*/service.py|*/controllers/**",
        "severity": "high",
        "suggested_fix": "Extract shared types to domain or pass parameters into utility functions instead of importing services.",
        "is_enabled": True,
        "is_system_inferred": True,
    },
    {
        "rule_code": "ARCH-005",
        "name": "Circular Dependencies Strictly Prohibited",
        "description": "Circular import chains between files or modules cause tight coupling, initialization order hazards, and maintainability degradation.",
        "rule_type": "no_circular_dependencies",
        "source_layer": None,
        "target_layer": None,
        "source_pattern": "**",
        "target_pattern": "**",
        "severity": "high",
        "suggested_fix": "Refactor common structures into a separate module or inject dependencies via interfaces or function arguments.",
        "is_enabled": True,
        "is_system_inferred": True,
    },
]


def detect_architecture_pattern(
    file_paths: List[str],
    frameworks: Optional[List[str]] = None,
    doc_contents: Optional[Dict[str, str]] = None,
) -> InferredPatternResult:
    """
    Examines file tree structure, cataloged frameworks, and documentation
    to infer the repository's primary architectural pattern with grounded confidence.
    """
    frameworks = [f.lower() for f in (frameworks or [])]
    doc_contents = doc_contents or {}
    clean_paths = [p.replace("\\", "/").lower() for p in file_paths]

    scores: Dict[str, float] = {
        "fullstack_monorepo": 0.0,
        "layered_mvc": 0.0,
        "clean_hexagonal": 0.0,
        "modular_monolith": 0.0,
        "component_based_spa": 0.0,
        "event_pipeline": 0.0,
    }
    evidence: Dict[str, List[str]] = {k: [] for k in scores}

    # 1. Monorepo / Fullstack check
    has_frontend = any(p.startswith("frontend/") or p.startswith("client/") or "/frontend/" in p for p in clean_paths)
    has_backend = any(p.startswith("backend/") or p.startswith("server/") or "/backend/" in p for p in clean_paths)
    if has_frontend and has_backend:
        scores["fullstack_monorepo"] += 3.5
        evidence["fullstack_monorepo"].append("Co-located frontend/ and backend/ directory trees detected.")

    # 2. Layered MVC check
    has_routes = any("/routes" in p or "/api" in p or "/controllers" in p for p in clean_paths)
    has_services = any("/services" in p or "service.py" in p or "/managers" in p for p in clean_paths)
    has_models = any("/models" in p or "models.py" in p or "/schemas" in p for p in clean_paths)

    if has_routes:
        scores["layered_mvc"] += 1.0
        evidence["layered_mvc"].append("Route/Controller layer present.")
    if has_services:
        scores["layered_mvc"] += 1.0
        evidence["layered_mvc"].append("Service business logic layer present.")
    if has_models:
        scores["layered_mvc"] += 1.0
        evidence["layered_mvc"].append("Data model/schema layer present.")

    if any(fw in ("fastapi", "flask", "django", "express", "rails", "spring") for fw in frameworks):
        scores["layered_mvc"] += 1.0
        evidence["layered_mvc"].append(f"Framework indicators: {', '.join(frameworks)}")

    # 3. Clean / Hexagonal / Ports-and-Adapters check
    has_domain = any("/domain" in p or "/entities" in p for p in clean_paths)
    has_usecases = any("/usecases" in p or "/use_cases" in p or "/application" in p for p in clean_paths)
    has_adapters = any("/adapters" in p or "/ports" in p or "/gateways" in p for p in clean_paths)
    has_infra = any("/infrastructure" in p or "/infra" in p for p in clean_paths)

    if has_domain and (has_usecases or has_adapters or has_infra):
        scores["clean_hexagonal"] += 3.0
        evidence["clean_hexagonal"].append("Dedicated domain/entities, usecases, or infrastructure ports detected.")

    # 4. Modular Monolith check
    # Multiple distinct high-level domains (e.g. auth, billing, catalog, orders)
    app_dirs = set()
    for p in clean_paths:
        m = re.match(r"^(?:backend/app|src|app)/([a-z0-9_\-]+)/", p)
        if m:
            app_dirs.add(m.group(1))

    if len(app_dirs) >= 4 and not has_domain:
        scores["modular_monolith"] += 3.5
        evidence["modular_monolith"].append(f"Independent bounded module packages detected: {sorted(list(app_dirs))[:5]}")

    # 5. Component-based SPA check (pure frontend repo)
    if (not has_backend) and (has_frontend or any(p.startswith("src/components") for p in clean_paths)):
        scores["component_based_spa"] += 3.0
        evidence["component_based_spa"].append("Component/Page SPA frontend hierarchy detected.")

    # 6. Event Pipeline check
    has_workers = any("/worker" in p or "/tasks" in p or "/queues" in p or "/consumers" in p for p in clean_paths)
    if has_workers:
        scores["event_pipeline"] += 1.5
        evidence["event_pipeline"].append("Worker/Task background processing modules detected.")

    # 7. Documentation inspection (ADRs / README)
    for doc_name, content in doc_contents.items():
        lower_content = content.lower()
        if "clean architecture" in lower_content or "hexagonal" in lower_content:
            scores["clean_hexagonal"] += 2.0
            evidence["clean_hexagonal"].append(f"Explicit Clean/Hexagonal documentation found in {doc_name}")
        if "mvc" in lower_content or "model-view-controller" in lower_content:
            scores["layered_mvc"] += 1.5
            evidence["layered_mvc"].append(f"MVC pattern references found in {doc_name}")
        if "modular monolith" in lower_content or "microservices" in lower_content:
            scores["modular_monolith"] += 2.0
            evidence["modular_monolith"].append(f"Modular architecture references found in {doc_name}")

    # Pick top pattern
    best_pattern = max(scores, key=scores.get)
    best_score = scores[best_pattern]

    if best_score == 0:
        best_pattern = "layered_mvc"
        confidence = 0.6
        ev = ["Standard multi-layer project structure."]
    else:
        # Normalize confidence to [0.65, 0.98]
        confidence = min(0.98, max(0.65, 0.65 + (best_score / 10.0) * 0.33))
        ev = evidence[best_pattern]

    DISPLAY_NAMES = {
        "fullstack_monorepo": "Fullstack Monorepo (Client / Server)",
        "layered_mvc": "Layered Multi-Tier (API / Service / Data)",
        "clean_hexagonal": "Clean Architecture / Hexagonal Ports & Adapters",
        "modular_monolith": "Modular Monolith (Bounded Contexts)",
        "component_based_spa": "Component-Driven Single Page Application",
        "event_pipeline": "Event-Driven & Worker Pipeline",
    }

    DESCRIPTIONS = {
        "fullstack_monorepo": "Co-locates frontend UI and backend API services with isolated boundaries and shared contracts.",
        "layered_mvc": "Separates concerns sequentially across Presentation/Routes, Business Service Logic, and Data Access/ORM models.",
        "clean_hexagonal": "Prioritizes inner core domain stability, decoupling business rules from external frameworks and delivery mechanisms.",
        "modular_monolith": "Organizes features into self-contained domain modules with clear package visibility.",
        "component_based_spa": "Structures client UI into declarative components, layouts, pages, and API client hooks.",
        "event_pipeline": "Processes asynchronous jobs and streams through decoupled producers, queues, and task consumers.",
    }

    return InferredPatternResult(
        pattern=best_pattern,
        display_name=DISPLAY_NAMES.get(best_pattern, best_pattern),
        confidence=round(confidence, 2),
        evidence=ev,
        suggested_rules=DEFAULT_BASELINE_RULES,
        description=DESCRIPTIONS.get(best_pattern, ""),
    )


# Alias for backward compatibility
infer_architecture_pattern = detect_architecture_pattern

