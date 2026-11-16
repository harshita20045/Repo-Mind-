"""
Layer and Module Classifier — RepoMind 2.0 Architecture Engine.

Classifies files, modules, and components into logical architectural layers:
  - presentation
  - business_logic
  - domain
  - data_access
  - infrastructure
  - shared_utility
  - frontend_ui
  - worker
  - test
"""
from typing import Dict, List, Optional
import re


LAYER_RANKS = {
    "presentation": 40,
    "frontend_ui": 40,
    "worker": 35,
    "business_logic": 30,
    "domain": 20,
    "data_access": 10,
    "infrastructure": 10,
    "shared_utility": 5,
    "test": 0,
    "unknown": 0,
}


def classify_layer(file_path: str) -> str:
    """Classifies a normalized file path into an architectural layer."""
    if not file_path:
        return "unknown"

    clean = file_path.replace("\\", "/").lower().strip("/")
    parts = clean.split("/")
    filename = parts[-1]

    # 1. Tests
    if any(p in clean for p in ("/tests/", "/test/", "/__tests__/", "/spec/")) or filename.startswith("test_") or filename.endswith((".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.ts")):
        return "test"

    # 2. Frontend UI
    if clean.startswith(("frontend/", "client/")) or any(p in clean for p in ("/components/", "/pages/", "/views/", "/layouts/", "/ui/")):
        return "frontend_ui"

    # 3. Worker / Background processing
    if any(p in clean for p in ("/worker/", "/workers/", "/tasks/", "/jobs/", "/queues/")):
        return "worker"

    # 4. Presentation / API / Controllers
    if any(p in clean for p in ("/routes", "/api", "/controllers", "/endpoints", "/views", "/handlers")) or filename in ("routes.py", "router.py", "endpoints.py", "controller.py"):
        return "presentation"

    # 5. Business Logic / Services
    if any(p in clean for p in ("/services", "/service", "/usecases", "/use_cases", "/managers", "/engine", "/pipeline")) or filename in ("service.py", "services.py", "engine.py", "manager.py"):
        return "business_logic"

    # 6. Domain / Core Entities
    if any(p in clean for p in ("/domain", "/entities", "/values", "/aggregates")) or filename in ("domain.py", "entities.py"):
        return "domain"

    # 7. Data Access / Models / Repositories
    if any(p in clean for p in ("/models", "/repository", "/repositories", "/dao", "/schemas", "/alembic", "/migrations")) or filename in ("models.py", "schemas.py", "repository.py"):
        return "data_access"

    # 8. Infrastructure / Clients / DB Connections
    if any(p in clean for p in ("/infrastructure", "/infra", "/clients", "/db", "/database", "/connectors", "/adapters", "/storage")):
        return "infrastructure"

    # 9. Shared Utility / Common / Helpers
    if any(p in clean for p in ("/utils", "/common", "/helpers", "/shared", "/lib", "/core", "/config")):
        return "shared_utility"

    return "business_logic" if clean.endswith(".py") else "unknown"


def get_layer_rank(layer: str) -> int:
    """Returns the relative hierarchy rank of a layer."""
    return LAYER_RANKS.get(layer, 0)
