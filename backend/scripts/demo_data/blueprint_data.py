"""
Developer Onboarding & Architecture Blueprint Data for RepoMind Demo.
Includes full 20-point business logic documentation for all modules,
4 role tracks, 4 execution flow traces, caution zones, safe starter areas,
and domain glossary.
"""

BLUEPRINT_DATA = {
    "architecture_pattern": "Layered Clean Architecture (Modular Monolith)",
    "summary": (
        "Enterprise-grade Order & User Management Platform designed with Layered Clean Architecture (Modular Monolith). "
        "Separates external HTTP routing (API), domain validation and business logic (Services), and persistence abstractions (Repositories) "
        "with strict dependency injection and isolated schema models. Implements transactional inventory deduction, idempotency checks, "
        "and multi-tenant user authentication."
    ),
    "subsystems": [
        {
            "name": "User Management & Authentication Subsystem",
            "path": "app/services/user_service.py",
            "purpose": (
                "Governs developer and customer identity, role-based access control (RBAC), password hashing with bcrypt, "
                "JWT session verification, and profile management."
            ),
            "key_files": [
                "app/api/users.py",
                "app/services/user_service.py",
                "app/models/user.py",
                "app/repositories/user_repository.py",
            ],
        },
        {
            "name": "Order Processing & Inventory Subsystem",
            "path": "app/services/order_service.py",
            "purpose": (
                "Orchestrates end-to-end checkout, line item pricing, stock reservation, status transitions "
                "(Pending -> Processing -> Shipped -> Delivered / Cancelled), and transactional inventory deduction."
            ),
            "key_files": [
                "app/api/orders.py",
                "app/services/order_service.py",
                "app/models/order.py",
                "app/repositories/order_repository.py",
            ],
        },
        {
            "name": "Core Application Bootstrap & Routing Tier",
            "path": "app/main.py",
            "purpose": (
                "Configures FastAPI application instance, mounts API routers with rate limiters, registers CORS policies, "
                "handles global exception formatting, and exposes healthcheck endpoints."
            ),
            "key_files": [
                "app/main.py",
                "app/config.py",
                "app/dependencies.py",
                "app/api/health.py",
            ],
        },
        {
            "name": "Data Access & In-Memory / PostgreSQL Repositories",
            "path": "app/repositories/order_repository.py",
            "purpose": (
                "Abstracts persistence storage operations, maintains transactional consistency, handles pagination, "
                "and prevents database leaks into domain services."
            ),
            "key_files": [
                "app/repositories/user_repository.py",
                "app/repositories/order_repository.py",
            ],
        },
        {
            "name": "Domain Entity Models & Schema Definitions",
            "path": "app/models/order.py",
            "purpose": (
                "Defines strongly-typed Pydantic V2 and dataclass models enforcing business invariants, status enums, "
                "field validations, and serialization rules."
            ),
            "key_files": [
                "app/models/user.py",
                "app/models/order.py",
            ],
        },
        {
            "name": "Automated Testing & Regression Suite",
            "path": "tests/test_orders.py",
            "purpose": (
                "Provides pytest fixtures, mock in-memory database states, unit test suites, integration test suites, "
                "and boundary validations across all application APIs."
            ),
            "key_files": [
                "tests/test_users.py",
                "tests/test_orders.py",
                "tests/test_health.py",
            ],
        },
    ],
    "request_flow": [
        {
            "step_number": 1,
            "layer": "HTTP Ingestion",
            "file": "app/main.py",
            "symbol": "app",
            "description": "Receives inbound HTTP request, applies CORS headers, and routes to path prefix.",
        },
        {
            "step_number": 2,
            "layer": "API Routing & Validation",
            "file": "app/api/orders.py",
            "symbol": "create_order",
            "description": "Parses JSON request body through Pydantic V2 schemas, verifying fields and types.",
        },
        {
            "step_number": 3,
            "layer": "Dependency Injection",
            "file": "app/dependencies.py",
            "symbol": "get_order_service",
            "description": "Resolves singleton repositories and injects configured OrderService instance.",
        },
        {
            "step_number": 4,
            "layer": "Business Domain Validation",
            "file": "app/services/order_service.py",
            "symbol": "OrderService.place_order",
            "description": "Enforces business invariants: verifies user existence, checks stock levels, calculates totals.",
        },
        {
            "step_number": 5,
            "layer": "Persistence & Storage",
            "file": "app/repositories/order_repository.py",
            "symbol": "OrderRepository.save",
            "description": "Persists new order record transactionally and atomically decrements inventory counts.",
        },
        {
            "step_number": 6,
            "layer": "Response Formatting",
            "file": "app/api/orders.py",
            "symbol": "create_order",
            "description": "Maps saved domain entity into OrderResponse DTO and returns HTTP 201 Created.",
        },
    ],
    "application_flows": {
        "startup": [
            {
                "step_number": 1,
                "layer": "Configuration Bootstrap",
                "file": "app/config.py",
                "symbol": "Settings",
                "description": "Loads environment variables, validates database connection strings and JWT secrets.",
            },
            {
                "step_number": 2,
                "layer": "FastAPI App Initialization",
                "file": "app/main.py",
                "symbol": "create_application",
                "description": "Instantiates FastAPI app with Swagger/OpenAPI metadata and global middleware.",
            },
            {
                "step_number": 3,
                "layer": "Router Mounting",
                "file": "app/main.py",
                "symbol": "app.include_router",
                "description": "Mounts health router, user router (/users), and order router (/orders).",
            },
            {
                "step_number": 4,
                "layer": "Storage Initialization",
                "file": "app/repositories/order_repository.py",
                "symbol": "init_storage",
                "description": "Initializes in-memory tables or verifies PostgreSQL relational connection pool.",
            },
        ],
        "api_lifecycle": [
            {
                "step_number": 1,
                "layer": "Request Routing",
                "file": "app/api/orders.py",
                "symbol": "get_order_by_id",
                "description": "Catches GET /orders/{order_id} request and parses path parameters.",
            },
            {
                "step_number": 2,
                "layer": "Authentication Check",
                "file": "app/dependencies.py",
                "symbol": "get_current_active_user",
                "description": "Extracts auth header, decodes user identity, and verifies account active status.",
            },
            {
                "step_number": 3,
                "layer": "Service Query",
                "file": "app/services/order_service.py",
                "symbol": "OrderService.get_order",
                "description": "Retrieves order entity and ensures requesting user owns the order or is an administrator.",
            },
            {
                "step_number": 4,
                "layer": "Repository Fetch",
                "file": "app/repositories/order_repository.py",
                "symbol": "OrderRepository.find_by_id",
                "description": "Executes indexed key lookup and hydrates domain Order model.",
            },
            {
                "step_number": 5,
                "layer": "HTTP 200 Serialization",
                "file": "app/api/orders.py",
                "symbol": "get_order_by_id",
                "description": "Serializes response model to JSON and emits HTTP 200 OK.",
            },
        ],
        "auth_flow": [
            {
                "step_number": 1,
                "layer": "Credentials Submission",
                "file": "app/api/users.py",
                "symbol": "login_for_access_token",
                "description": "Client submits username and password payload via POST /users/login.",
            },
            {
                "step_number": 2,
                "layer": "Password Verification",
                "file": "app/services/user_service.py",
                "symbol": "UserService.authenticate_user",
                "description": "Fetches user by email, verifies bcrypt password hash using constant-time comparison.",
            },
            {
                "step_number": 3,
                "layer": "Token Generation",
                "file": "app/dependencies.py",
                "symbol": "create_access_token",
                "description": "Signs HMAC-SHA256 JWT access token with user_id, role, and expiration claim.",
            },
            {
                "step_number": 4,
                "layer": "Subsequent Request Verification",
                "file": "app/dependencies.py",
                "symbol": "get_current_user",
                "description": "Validates Bearer token on protected endpoints, populating user context into request.",
            },
        ],
        "db_flow": [
            {
                "step_number": 1,
                "layer": "Repository Invocation",
                "file": "app/repositories/order_repository.py",
                "symbol": "OrderRepository.save",
                "description": "Receives validated Order domain entity from service layer.",
            },
            {
                "step_number": 2,
                "layer": "Transaction Isolation",
                "file": "app/repositories/order_repository.py",
                "symbol": "transaction_scope",
                "description": "Acquires lock or begins isolated database transaction block.",
            },
            {
                "step_number": 3,
                "layer": "Entity Persistence",
                "file": "app/repositories/order_repository.py",
                "symbol": "insert_or_update",
                "description": "Writes order header and order items into persistence store.",
            },
            {
                "step_number": 4,
                "layer": "Commit & Release",
                "file": "app/repositories/order_repository.py",
                "symbol": "commit_transaction",
                "description": "Flushes changes, commits transaction, and returns persisted entity.",
            },
        ],
    },
    "lifecycle_diagram": """sequenceDiagram
    autonumber
    actor Client as Web Client / API Caller
    participant Router as API Router (app/api/orders.py)
    participant Dep as Dependencies (app/dependencies.py)
    participant Service as Order Service (app/services/order_service.py)
    participant Repo as Order Repository (app/repositories/order_repository.py)
    participant DB as Storage Engine (PostgreSQL / In-Memory)

    Client->>Router: POST /orders (CreateOrderRequest)
    Router->>Dep: get_current_user() & get_order_service()
    Dep-->>Router: Authenticated User + Injected OrderService
    Router->>Service: place_order(user_id, items, shipping_address)
    Service->>Service: Validate stock availability & calculate discounts
    Service->>Repo: save(order_entity)
    Repo->>DB: INSERT order & line_items (atomic transaction)
    DB-->>Repo: Order row saved (ID: #4082)
    Repo-->>Service: Persisted Order entity
    Service-->>Router: Order domain model (Status: Confirmed)
    Router-->>Client: 201 Created (OrderResponse JSON)
""",
    "mermaid_diagram": """flowchart TD
    subgraph ClientLayer["Presentation & Clients"]
        WebUI["Web Application (React 18)"]
        ExternalAPI["External API Consumers"]
    end

    subgraph APILayer["FastAPI API Routing (app/api)"]
        UsersRouter["users.py (/users)"]
        OrdersRouter["orders.py (/orders)"]
        HealthRouter["health.py (/health)"]
    end

    subgraph ServiceLayer["Domain Services (app/services)"]
        UserService["user_service.py (UserService)"]
        OrderService["order_service.py (OrderService)"]
    end

    subgraph RepositoryLayer["Data Repositories (app/repositories)"]
        UserRepo["user_repository.py (UserRepository)"]
        OrderRepo["order_repository.py (OrderRepository)"]
    end

    subgraph ModelLayer["Domain Models (app/models)"]
        UserModel["user.py (User, UserCreate, UserRole)"]
        OrderModel["order.py (Order, OrderItem, OrderStatus)"]
    end

    subgraph StorageLayer["Persistence Tier"]
        DB[("PostgreSQL / In-Memory Store")]
    end

    WebUI --> APILayer
    ExternalAPI --> APILayer
    UsersRouter --> UserService
    OrdersRouter --> OrderService
    UserService --> UserRepo
    OrderService --> OrderRepo
    OrderService --> UserRepo
    UserService -.-> UserModel
    OrderService -.-> OrderModel
    UserRepo --> DB
    OrderRepo --> DB
""",
    "caution_zones": [
        {
            "path": "app/services/order_service.py",
            "risk_level": "critical",
            "reason": (
                "Governs order status transitions, inventory stock reservations, and monetary pricing calculations. "
                "Concurrency errors here cause double-spending or inventory underflow."
            ),
        },
        {
            "path": "app/dependencies.py",
            "risk_level": "high",
            "reason": (
                "Handles cryptographic JWT signing, password verification, and dependency resolution. "
                "Any regression risks authentication bypass or token exposure."
            ),
        },
        {
            "path": "app/models/order.py",
            "risk_level": "high",
            "reason": (
                "Defines core domain schema and field invariants. Breaking changes here cascade into API contracts "
                "and database persistence schemas."
            ),
        },
        {
            "path": "app/main.py",
            "risk_level": "medium",
            "reason": (
                "App bootstrap, global middleware, and CORS policies. Modifying configuration can lead to security misconfigurations "
                "or server startup failures."
            ),
        },
    ],
    "safe_starter_areas": [
        {
            "area": "Healthcheck & System Diagnostics (app/api/health.py)",
            "description": (
                "Isolated monitoring endpoint returning application uptime, database connectivity status, and version metadata. "
                "Zero risk of mutating business domain data."
            ),
            "starter_ideas": [
                "Add memory usage diagnostics to GET /health.",
                "Include database ping latency in the healthcheck response payload.",
                "Add an uptime counter in seconds since server bootstrap.",
            ],
        },
        {
            "area": "Unit & Integration Test Suite (tests/)",
            "description": (
                "Well-isolated pytest test cases covering user creation, order calculation, and error scenarios with clean fixtures."
            ),
            "starter_ideas": [
                "Add parameterized test for invalid order item quantities (zero or negative).",
                "Write a test verifying order status transition rejection from 'delivered' back to 'pending'.",
                "Add fixture testing expired JWT token rejection with HTTP 401.",
            ],
        },
        {
            "area": "User Profile Validation Enhancements (app/models/user.py)",
            "description": (
                "Pydantic schema definitions with standard regex field validators. Easy to read and safe to enhance."
            ),
            "starter_ideas": [
                "Add phone number format validation regex to UserProfile schema.",
                "Enforce minimum password complexity validator (minimum 8 chars, 1 number, 1 special char).",
            ],
        },
    ],
    "glossary": [
        {
            "term": "OrderLifecycle",
            "category": "domain",
            "definition": "The formal finite state machine governing an order: PENDING -> PROCESSING -> SHIPPED -> DELIVERED (or CANCELLED).",
            "related_files": ["app/models/order.py", "app/services/order_service.py"],
        },
        {
            "term": "IdempotencyKey",
            "category": "architecture",
            "definition": "A unique client-supplied token (UUIDv4) preventing duplicate charge or order creation during network retries.",
            "related_files": ["app/api/orders.py", "app/services/order_service.py"],
        },
        {
            "term": "ModularMonolith",
            "category": "architecture",
            "definition": "An architectural pattern where all modules share a unified runtime and codebase, but enforce strict boundaries between API, Service, and Repository layers.",
            "related_files": ["app/main.py", "app/config.py", "Docs/02-architecture/architecture-decisions.md"],
        },
        {
            "term": "RBACPermission",
            "category": "domain",
            "definition": "Role-Based Access Control permission matrix (Org Admin, Team Lead, Reviewer, Developer) enforced server-side.",
            "related_files": ["app/dependencies.py", "app/api/users.py"],
        },
        {
            "term": "OptimisticLocking",
            "category": "infrastructure",
            "definition": "A concurrency control technique that uses a version column to prevent concurrent overwrites without blocking read operations.",
            "related_files": ["app/repositories/order_repository.py", "app/models/order.py"],
        },
        {
            "term": "BlastRadius",
            "category": "architecture",
            "definition": "The maximum extent of architectural and functional impact that a bug, crash, or breaking change in a module can cause across the system.",
            "related_files": ["app/dependencies.py", "app/services/order_service.py"],
        },
        {
            "term": "CoverageGap",
            "category": "testing",
            "definition": "An unexercised code path, branch, or edge case identified by AI Test Intelligence lacking dedicated unit or integration assertions.",
            "related_files": ["tests/test_orders.py", "tests/test_users.py"],
        },
        {
            "term": "RFC7807ProblemDetails",
            "category": "domain",
            "definition": "Standardized JSON error format for HTTP APIs containing type, title, status, detail, and instance URI fields.",
            "related_files": ["app/main.py", "app/api/orders.py"],
        },
    ],
    "tracks": {
        "backend": {
            "track_name": "backend",
            "reading_order": [
                {
                    "file_path": "app/main.py",
                    "role": "Application Bootstrap & Router Setup",
                    "why_read": "Understand how FastAPI initializes, how middleware is applied, and how API routers are mounted.",
                    "focus_symbols": ["app", "create_application"],
                    "key_lines": "L1-L65",
                    "responsibilities": "Registers routes, CORS, global error handling, and server entry point.",
                    "important_functions": ["create_application", "lifespan"],
                    "dependencies": ["app.api.users", "app.api.orders", "app.api.health"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "app/dependencies.py",
                    "role": "Dependency Injection & Security Context",
                    "why_read": "Learn how database sessions, repositories, services, and authenticated users are injected into FastAPI endpoints.",
                    "focus_symbols": ["get_current_user", "get_order_service", "get_user_service"],
                    "key_lines": "L15-L85",
                    "responsibilities": "Resolves request scoped services, decodes JWT tokens, and gates access.",
                    "important_functions": ["get_current_user", "get_current_active_user", "create_access_token"],
                    "dependencies": ["app.services.user_service", "app.services.order_service"],
                    "relevant_documentation": "docs/security.md",
                },
                {
                    "file_path": "app/models/order.py",
                    "role": "Order Domain Entities & Schema Definitions",
                    "why_read": "Inspect the core domain models, order status enums, line items, and Pydantic validation rules.",
                    "focus_symbols": ["Order", "OrderItem", "OrderStatus", "OrderCreate"],
                    "key_lines": "L10-L75",
                    "responsibilities": "Defines domain data invariants, status states, and JSON serialization schemas.",
                    "important_functions": ["calculate_total", "validate_items"],
                    "dependencies": ["pydantic", "enum"],
                    "relevant_documentation": "docs/api-contract.md",
                },
                {
                    "file_path": "app/services/order_service.py",
                    "role": "Order Processing Business Logic",
                    "why_read": "This is the primary business logic engine. Study how orders are placed, stock is verified, and state transitions occur.",
                    "focus_symbols": ["OrderService", "place_order", "cancel_order", "update_order_status"],
                    "key_lines": "L25-L160",
                    "responsibilities": "Enforces business rules, inventory deduction, pricing totals, and order lifecycle transitions.",
                    "important_functions": ["place_order", "cancel_order", "get_order_by_id", "list_user_orders"],
                    "dependencies": ["app.repositories.order_repository", "app.models.order"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "app/repositories/order_repository.py",
                    "role": "Order Data Persistence Layer",
                    "why_read": "Understand persistence mechanics, transactional operations, and in-memory/Postgres data management.",
                    "focus_symbols": ["OrderRepository", "save", "find_by_id", "find_by_user_id"],
                    "key_lines": "L15-L110",
                    "responsibilities": "Performs atomic database queries, manages storage records, and encapsulates persistence queries.",
                    "important_functions": ["save", "find_by_id", "find_by_user", "delete"],
                    "dependencies": ["app.models.order"],
                    "relevant_documentation": "docs/database.md",
                },
                {
                    "file_path": "app/api/orders.py",
                    "role": "Order REST API Controller",
                    "why_read": "See how incoming HTTP requests are validated, handed off to OrderService, and formatted into API responses.",
                    "focus_symbols": ["router", "create_order", "get_order", "list_orders"],
                    "key_lines": "L20-L95",
                    "responsibilities": "Exposes /orders REST endpoints, validates request payloads, and handles HTTP status codes.",
                    "important_functions": ["create_order", "get_order", "cancel_order"],
                    "dependencies": ["app.services.order_service", "app.dependencies"],
                    "relevant_documentation": "docs/api-contract.md",
                },
                {
                    "file_path": "tests/test_orders.py",
                    "role": "Order Test Suite & Behavioral Assertions",
                    "why_read": "Verify how orders behave under normal, boundary, and error conditions using pytest.",
                    "focus_symbols": ["test_create_order_success", "test_insufficient_stock", "test_order_not_found"],
                    "key_lines": "L10-L120",
                    "responsibilities": "Automates verification of order placement, status updates, and edge cases.",
                    "important_functions": ["test_create_order_success", "test_insufficient_stock"],
                    "dependencies": ["pytest", "app.main"],
                    "relevant_documentation": "docs/architecture.md",
                },
            ],
            "milestones": [
                {
                    "id": "be_setup_1",
                    "title": "Validate Environment & Health Endpoint",
                    "description": "Start the backend application locally and verify that the /health endpoint responds with HTTP 200 OK.",
                    "action_type": "run_command",
                    "action_hint": "curl http://localhost:8000/health",
                    "practical_task": "Confirm that health endpoint returns service status, uptime, and database connection state.",
                },
                {
                    "id": "be_inspect_2",
                    "title": "Inspect OrderService State Machine",
                    "description": "Open app/services/order_service.py and trace the allowed transitions in update_order_status.",
                    "action_type": "code_inspection",
                    "action_hint": "app/services/order_service.py:75",
                    "practical_task": "Identify why an order in 'delivered' state cannot be transitioned to 'cancelled'.",
                },
                {
                    "id": "be_test_3",
                    "title": "Execute Order and User Test Suites",
                    "description": "Run the automated pytest test suite to ensure all unit and integration tests pass without regression.",
                    "action_type": "run_command",
                    "action_hint": "pytest tests/test_orders.py tests/test_users.py -v",
                    "practical_task": "Verify that all 14 tests pass and review the mock repository fixtures.",
                },
                {
                    "id": "be_first_task_4",
                    "title": "Implement Discount Code Validation (First Contribution)",
                    "description": "Add support for an optional promo_code string in OrderCreate schema that applies a 10% discount.",
                    "action_type": "first_task",
                    "action_hint": "app/models/order.py -> app/services/order_service.py",
                    "practical_task": "Add promo_code field in OrderCreate, calculate discounted total in OrderService, and add a unit test.",
                },
            ],
        },
        "frontend": {
            "track_name": "frontend",
            "reading_order": [
                {
                    "file_path": "frontend/src/App.jsx",
                    "role": "Single Page Application Root & Router",
                    "why_read": "Understand route definitions, authentication session state, and navigation layout.",
                    "focus_symbols": ["App", "ProtectedRoute", "checkSession"],
                    "key_lines": "L45-L165",
                    "responsibilities": "Mounts React Router routes, manages session token lifecycle, handles logout.",
                    "important_functions": ["checkSession", "handleLoginSuccess", "handleLogout"],
                    "dependencies": ["react-router-dom", "frontend/src/lib/api.js"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "frontend/src/lib/api.js",
                    "role": "Central HTTP API Client & SDK",
                    "why_read": "Learn how the frontend communicates with the backend, sends HttpOnly credentials, and handles 401/403 errors.",
                    "focus_symbols": ["apiRequest", "historyApi", "onboardingApi", "intelligenceApi"],
                    "key_lines": "L1-L150",
                    "responsibilities": "Encapsulates fetch calls, attaches Bearer credentials, parses errors into readable messages.",
                    "important_functions": ["apiRequest", "authApi.login", "historyApi.compareChanges"],
                    "dependencies": ["fetch"],
                    "relevant_documentation": "docs/api-contract.md",
                },
                {
                    "file_path": "frontend/src/pages/CodebaseGuidePage.jsx",
                    "role": "Developer Onboarding & Architecture Blueprint View",
                    "why_read": "Inspect how architecture flows, tracks, reading lists, caution zones, and personal milestones render.",
                    "focus_symbols": ["CodebaseGuidePage", "handleToggleMilestone", "handleTrackChange"],
                    "key_lines": "L30-L240",
                    "responsibilities": "Renders interactive onboarding tracks, Mermaid diagrams, and private developer scratchpad.",
                    "important_functions": ["handleToggleMilestone", "handleTrackChange", "handleNotesChange"],
                    "dependencies": ["@tanstack/react-query", "MermaidViewer"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "frontend/src/pages/HistoricalIntelligencePage.jsx",
                    "role": "Historical Code Intelligence & ADR Explorer",
                    "why_read": "Understand how historical PR records, git commits, recurring hotspots, and ADRs are visualized.",
                    "focus_symbols": ["HistoricalIntelligencePage", "handleRunComparison"],
                    "key_lines": "L20-L150",
                    "responsibilities": "Provides searchable tabs for PR history, recurring bug hotspots, and ADR records.",
                    "important_functions": ["handleRunComparison", "triggerIndex"],
                    "dependencies": ["historyApi", "@tanstack/react-query"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "frontend/src/pages/RepositoryTopologyPage.jsx",
                    "role": "Repository Topology & Code Knowledge Graph",
                    "why_read": "Explore AST symbols, dependencies, and relational architectural diagrams.",
                    "focus_symbols": ["RepositoryTopologyPage", "ArchitectureDashboard"],
                    "key_lines": "L25-L160",
                    "responsibilities": "Visualizes call graphs, AST code nodes, and rule violations.",
                    "important_functions": ["triggerIndexMutation"],
                    "dependencies": ["intelligenceApi", "architectureApi"],
                    "relevant_documentation": "docs/architecture.md",
                },
            ],
            "milestones": [
                {
                    "id": "fe_setup_1",
                    "title": "Start Vite Dev Server & Connect to Backend",
                    "description": "Start the React development server locally on port 5173 and verify that the login page renders.",
                    "action_type": "run_command",
                    "action_hint": "cd frontend && npm run dev",
                    "practical_task": "Confirm that the login page renders with modern Dark Theme styling without console errors.",
                },
                {
                    "id": "fe_explore_2",
                    "title": "Explore Codebase Guide & Select Learning Track",
                    "description": "Navigate to /repositories/1/guide, select the 'Frontend Track', and inspect your reading order.",
                    "action_type": "code_inspection",
                    "action_hint": "frontend/src/pages/CodebaseGuidePage.jsx",
                    "practical_task": "Check off your first onboarding milestone and verify that the progress meter updates.",
                },
            ],
        },
        "fullstack": {
            "track_name": "fullstack",
            "reading_order": [
                {
                    "file_path": "app/main.py",
                    "role": "Backend Application Entry Point",
                    "why_read": "Understand server lifecycle, route mounting, and CORS middleware setup.",
                    "focus_symbols": ["app"],
                    "key_lines": "L1-L65",
                    "responsibilities": "Initializes API and defines router endpoints.",
                    "important_functions": ["create_application"],
                    "dependencies": ["app.api"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "frontend/src/lib/api.js",
                    "role": "Frontend API Client SDK",
                    "why_read": "Trace how frontend requests map to backend route endpoints.",
                    "focus_symbols": ["apiRequest"],
                    "key_lines": "L1-L120",
                    "responsibilities": "Provides client-side fetch abstractions and error translation.",
                    "important_functions": ["apiRequest"],
                    "dependencies": ["fetch"],
                    "relevant_documentation": "docs/api-contract.md",
                },
                {
                    "file_path": "app/api/orders.py",
                    "role": "Order API Router",
                    "why_read": "Review contract definitions and response payloads consumed by frontend views.",
                    "focus_symbols": ["create_order", "get_order"],
                    "key_lines": "L15-L80",
                    "responsibilities": "HTTP handling for orders.",
                    "important_functions": ["create_order"],
                    "dependencies": ["app.services.order_service"],
                    "relevant_documentation": "docs/api-contract.md",
                },
                {
                    "file_path": "frontend/src/pages/ReviewPage.jsx",
                    "role": "PR Code Review & Risk Dashboard",
                    "why_read": "Learn how AI findings, change impact graphs, and test scenarios are unified.",
                    "focus_symbols": ["ReviewPage", "ApprovalModal"],
                    "key_lines": "L30-L200",
                    "responsibilities": "Interactive PR review workspace.",
                    "important_functions": ["triggerReview", "submitDecision"],
                    "dependencies": ["reviewApi", "impactApi", "testingApi"],
                    "relevant_documentation": "docs/architecture.md",
                },
            ],
            "milestones": [
                {
                    "id": "fs_setup_1",
                    "title": "Validate End-to-End API Communication",
                    "description": "Log into the frontend using admin@example.com and verify that the repositories dashboard populates.",
                    "action_type": "run_command",
                    "action_hint": "Open http://localhost:5173 and log in with Password123!",
                    "practical_task": "Confirm that repository #1 shows status 'Indexed' and displays accurate AST node counts.",
                },
            ],
        },
        "qa": {
            "track_name": "qa",
            "reading_order": [
                {
                    "file_path": "tests/test_orders.py",
                    "role": "Order Integration Test Suite",
                    "why_read": "Review existing test assertions, fixture setups, and order placement test cases.",
                    "focus_symbols": ["test_create_order_success", "test_insufficient_stock"],
                    "key_lines": "L1-L115",
                    "responsibilities": "Validates order business logic and error handling.",
                    "important_functions": ["test_create_order_success", "test_order_not_found"],
                    "dependencies": ["pytest", "app.services.order_service"],
                    "relevant_documentation": "docs/architecture.md",
                },
                {
                    "file_path": "tests/test_users.py",
                    "role": "User & Authentication Test Suite",
                    "why_read": "Understand password hashing verification, duplicate user detection, and authentication tests.",
                    "focus_symbols": ["test_create_user_success", "test_duplicate_email"],
                    "key_lines": "L1-L85",
                    "responsibilities": "Validates user registration and security checks.",
                    "important_functions": ["test_create_user_success", "test_authenticate_user"],
                    "dependencies": ["pytest", "app.services.user_service"],
                    "relevant_documentation": "docs/security.md",
                },
                {
                    "file_path": "tests/test_health.py",
                    "role": "Healthcheck & Smoke Test",
                    "why_read": "Basic availability smoke test for CI/CD pipelines.",
                    "focus_symbols": ["test_health_returns_200"],
                    "key_lines": "L1-L25",
                    "responsibilities": "Verifies server responds to health probes.",
                    "important_functions": ["test_health_returns_200"],
                    "dependencies": ["pytest", "httpx"],
                    "relevant_documentation": "docs/architecture.md",
                },
            ],
            "milestones": [
                {
                    "id": "qa_setup_1",
                    "title": "Run Full Pytest Test Suite with Coverage",
                    "description": "Execute all tests and generate a line coverage report.",
                    "action_type": "run_command",
                    "action_hint": "pytest tests/ --cov=app --cov-report=term-missing",
                    "practical_task": "Identify any service functions with less than 80% branch coverage.",
                },
            ],
        },
    },
}
