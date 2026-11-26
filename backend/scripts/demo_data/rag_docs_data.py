"""
Comprehensive RAG Knowledge Documents for RepoMind Demo.
Provides grounded documentation chunks for semantic search and AI Assistant
to answer all 10 corporate presentation questions with high accuracy.
"""

RAG_DOCUMENTS = [
    {
        "path": "docs/business-logic-specification.md",
        "title": "Complete Business Logic & Module Workflow Specification",
        "content": """# RepoMind — Complete Business Logic & Module Workflow Specification

## 1. Project Purpose & Business Overview
RepoMind's target application is an enterprise-grade Order and User Management Platform designed with Layered Clean Architecture. It provides resilient customer registration, authentication, inventory stock management, and atomic order placement.

## 2. Complete End-to-End Business Workflow
The complete business workflow executes across four distinct phases:
1. **User Registration & Identity Provisioning**:
   - Customer submits email, full name, and password via `POST /users`.
   - Backend checks `UserRepository` for existing accounts with the same email.
   - If unique, password is encrypted using `bcrypt` with work factor 12 (ADR-016).
   - User entity is created in `PENDING_VERIFICATION` or `ACTIVE` state.
2. **Authentication & Session Issuance**:
   - Customer submits credentials via `POST /users/login`.
   - `UserService.authenticate_user` checks password using constant-time verification to prevent timing attacks.
   - On success, an HMAC-SHA256 JWT access token is signed containing user ID, role, and 60-minute expiration.
3. **Cart Assembly & Order Checkout**:
   - Customer submits order items, quantities, shipping address, and `X-Idempotency-Key` header via `POST /orders`.
   - `OrderService.place_order` verifies stock availability in warehouse inventory for every requested product.
   - Pricing calculations compute line item subtotals (`quantity * unit_price`), volume discounts for orders > $500, and final order total using two-decimal rounding.
4. **Atomic Inventory Reservation & Persistence**:
   - `OrderRepository` starts an isolated database transaction.
   - Available stock is atomically decremented.
   - The Order entity is persisted in `PENDING` state and returned with HTTP 201 Created.
5. **Fulfillment & Lifecycle Transitions**:
   - Orders transition through formal states: `PENDING` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED`.
   - If an order is cancelled prior to shipment, `OrderService.cancel_order` automatically releases reserved stock back to inventory (BUG-142 resolution).

## 3. Module Responsibilities & Business Rules
- **app/api/users.py**: Ingestion controller for user registration, login, and profile retrieval.
- **app/api/orders.py**: Ingestion controller for order placement, paginated history, and cancellation. Enforces IDOR authorization checks (PR #13) so users only see their own orders.
- **app/services/user_service.py**: Core user domain logic, credential validation, constant-time verification.
- **app/services/order_service.py**: Core monetary checkout engine, state machine transitions, volume tier discounts, inventory reservation.
- **app/repositories/user_repository.py**: Data access layer for user persistence.
- **app/repositories/order_repository.py**: Data access layer for atomic order persistence and inventory locking.
- **app/models/user.py**: Pydantic V2 schemas (`UserCreate`, `UserResponse`) with field validators.
- **app/models/order.py**: Pydantic V2 schemas (`OrderCreate`, `OrderItem`, `OrderStatus`) rejecting empty item lists (BUG-188 resolution).
- **app/dependencies.py**: Dependency injection container resolving services, DB connections, and validating JWT bearer tokens.
""",
    },
    {
        "path": "docs/architecture-overview.md",
        "title": "System Architecture, Layer Dependencies, and Technical Decisions",
        "content": """# RepoMind — System Architecture & Layer Dependencies

## 1. Architectural Pattern: Layered Clean Architecture (Modular Monolith)
The application adheres strictly to Clean Architecture principles (ADR-001, ADR-013):
- **API Routing Layer (`app/api`)**: Responsible exclusively for HTTP parameter parsing, validation, and status codes. Must NEVER query database models directly.
- **Domain Service Layer (`app/services`)**: Contains pure business logic, calculations, domain invariants, and lifecycle transitions. Communicates only through Repository interfaces.
- **Data Access Layer (`app/repositories`)**: Encapsulates all database operations, SQL queries, and storage transaction scopes.
- **Entity Schemas (`app/models`)**: Strongly typed Pydantic V2 models defining domain invariants.

## 2. Dependency Flow & Graph Relationships
- Incoming callers: `app/main.py` -> `app/api/orders.py` -> `app/services/order_service.py` -> `app/repositories/order_repository.py`.
- `OrderService` depends on:
  1. `OrderRepository`: For saving and querying order records.
  2. `UserRepository`: For verifying customer account status.
  3. `Order` and `OrderItem` models: For domain schema validation.
- Cross-layer boundary rules:
  - Rule `ARCH-LAYER-01`: API layer routes MUST NOT import or query repositories directly.
  - Rule `ARCH-LAYER-02`: Domain services MUST NOT import FastAPI request or response objects.
  - Rule `ARCH-CONCURRENCY-01`: Inventory decrement MUST execute within an atomic transaction with idempotency key checks.

## 3. Database Interaction & Tables
- `orders`: Stores order headers (`id`, `user_id`, `status`, `total_amount`, `idempotency_key`, `created_at`).
- `order_items`: Stores order line items (`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `subtotal`).
- `users`: Stores user credentials and profile records (`id`, `email`, `password_hash`, `role`, `created_at`).
- `inventory`: Tracks available warehouse product stock (`product_id`, `available_quantity`, `reserved_quantity`).
""",
    },
    {
        "path": "docs/historical-decisions-log.md",
        "title": "Historical Decisions, Architectural Evolution, and Bug Log",
        "content": """# RepoMind — Historical Decisions, Architectural Evolution, and Bug Log

## 1. Why Was OrderService Refactored?
In PR #4 (commit `18293a4b`), `OrderService` was extensively refactored to decouple it from direct database access into the `OrderRepository` layer.
- **Problem**: In early versions, `OrderService` executed raw database queries directly, tightly coupling business logic with SQL queries and making unit testing impossible without an active database.
- **Solution**: Extracted `OrderRepository` interface per ADR-013 (Clean Architecture). Service methods now interact only with repository interfaces.
- **Outcome**: Unit tests can now mock `OrderRepository` completely, reducing test execution time from 4.2s to 0.18s.

## 2. Which PR Introduced the Database Schema Changes?
- PR #2: Introduced initial `orders` and `order_items` tables.
- PR #6: Added `order_status` ENUM (`PENDING`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`).
- PR #9: Added `idempotency_key` unique column to `orders` table to support client idempotency tokens per ADR-014.
- PR #16: Added `audit_events` table tracking historical status transitions.

## 3. Historical Bug Intelligence & Recurring Issues
- **BUG-101 (PR #3, commit `f6071829`)**: Inventory race condition under concurrent checkouts. Resolution: Added atomic decrement locks in `OrderRepository` per ADR-014.
- **BUG-109 (PR #5, commit `293a4b5c`)**: Floating-point decimal rounding discrepancies in multi-item orders. Resolution: Enforced `round(val, 2)` on all monetary calculations.
- **BUG-142 (PR #10, commit `8f901a2b`)**: Missing inventory restock on order cancellation. Resolution: Added stock release callback in `OrderService.cancel_order`.
- **SEC-14 (PR #13, commit `2b3c4d5e`)**: IDOR vulnerability allowing users to view other customers' orders. Resolution: Validated `current_user.id == order.user_id` in API controller.
- **BUG-188 (PR #15, commit `5e6f7a8b`)**: Empty order items array accepted without validation error. Resolution: Added `@field_validator` requiring at least 1 item.

## 4. Governing Architecture Decision Records (ADRs)
- **ADR-001**: Modular Monolith Architecture.
- **ADR-003**: FastAPI + Pydantic V2 for API validation.
- **ADR-013**: Layered Clean Architecture (API -> Service -> Repository).
- **ADR-014**: Atomic Inventory Deduction and Idempotency Key Tracking.
- **ADR-015**: RFC 7807 Problem Details for Error Responses.
- **ADR-016**: Bcrypt password hashing with constant-time verification.
""",
    },
    {
        "path": "docs/developer-onboarding-guide.md",
        "title": "New Developer Onboarding Guide & Frequently Asked Questions",
        "content": """# RepoMind — New Developer Onboarding Guide & FAQ

## 1. What a New Developer Must Understand Before Modifying Modules
Before modifying any module in this codebase, remember:
1. **Never bypass the Repository layer**: Route handlers must call Services, and Services must call Repositories. Direct database queries from route handlers violate rule `ARCH-LAYER-01`.
2. **OrderService is a Critical Caution Zone**: It governs money and inventory. Modifying stock deduction requires running concurrency tests (`pytest tests/test_orders.py -k test_concurrency`).
3. **Always Return RFC 7807 Errors**: Never raise bare strings or custom dictionaries on error. Use domain exceptions handled by `app/main.py`.
4. **Idempotency is Mandatory**: Checkout and payment endpoints must accept and respect the `X-Idempotency-Key` header.
5. **Preserve IDOR Authorization**: Endpoints accepting an ID parameter must assert that the authenticated user owns the resource or is an admin.

## 2. Impact of Changing APIs
- Modifying `POST /orders` payload: Any changes to `OrderCreate` schema cascade into client checkout forms, Swagger contracts, and `test_orders.py`. Always make new fields optional or provide sensible defaults.
- Modifying `GET /health`: Safe starter area with zero downstream business impact.

## 3. Frequently Asked Questions (FAQ)
- **Q: How do I run the test suite locally?**
  Run `pytest tests/ -v`. All 20+ unit and integration tests should pass within 1.5 seconds.
- **Q: Where is authentication configured?**
  In `app/dependencies.py` via `get_current_user` and `create_access_token`.
- **Q: How are database transactions handled?**
  Inside `app/repositories/order_repository.py` using scoped context managers.
- **Q: How do I test with mock data?**
  Pytest fixtures in `tests/test_orders.py` provide pre-seeded in-memory repositories with mock users and products.
""",
    },
]
