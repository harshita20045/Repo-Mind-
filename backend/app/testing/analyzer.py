"""
AI Test Intelligence Analyzer — RepoMind 2.0.

Analyzes modified functions/methods in pull requests, inspects existing test suites,
detects missing test coverage gaps, traces impacted APIs and services via the Code Knowledge Graph,
and generates structured test scenarios across 8 standard categories.
"""
import ast
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.testing.models import TestScenario
from backend.app.github.models import PullRequest
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.rag.models import Document
from backend.app.review.analysis import parse_diff_hunks, PRDiffHunk
from backend.app.impact.detector import detect_code_changes

logger = logging.getLogger("repomind.testing.analyzer")

TEST_CATEGORIES = [
    "positive",
    "negative",
    "boundary",
    "validation",
    "authentication",
    "authorization",
    "integration",
    "regression",
]


class TestIntelligenceAnalyzer:
    """
    Analyzes code changes and existing repository tests to produce actionable,
    grounded test scenarios.
    """
    __test__ = False

    def __init__(self, db: Session, repository_id: int):
        self.db = db
        self.repository_id = repository_id

    def analyze(
        self,
        diff: str,
        pull_request_id: Optional[int] = None,
        review_run_id: Optional[int] = None,
    ) -> List[TestScenario]:
        """
        Full orchestration of AI Test Intelligence analysis.
        """
        # 1. Parse diff hunks and identify modified files and line ranges
        diff_hunks_by_file = parse_diff_hunks(diff)
        changed_files = list(diff_hunks_by_file.keys())

        if not changed_files:
            return []

        # 2. Extract modified functions, methods, and classes
        modified_symbols = self._extract_modified_symbols(diff, diff_hunks_by_file)

        # 3. Discover and inspect existing repository test files
        existing_test_catalog = self._discover_existing_tests()

        # 4. For each modified symbol, trace impacted APIs, detect coverage gaps,
        #    and assemble 8-category test scenarios
        generated_scenarios: List[TestScenario] = []

        # Clean up previous scenarios for this PR / review run if present
        if pull_request_id:
            self.db.execute(
                delete(TestScenario).where(
                    TestScenario.repository_id == self.repository_id,
                    TestScenario.pull_request_id == pull_request_id,
                )
            )
        elif review_run_id:
            self.db.execute(
                delete(TestScenario).where(
                    TestScenario.repository_id == self.repository_id,
                    TestScenario.review_run_id == review_run_id,
                )
            )

        for sym in modified_symbols:
            file_path = sym["file_path"]
            symbol_name = sym["name"]
            symbol_type = sym.get("type", "function")
            signature = sym.get("signature", "")
            is_endpoint = sym.get("is_endpoint", False) or "route" in file_path.lower() or "api" in file_path.lower()

            # Find existing related test file if present
            matching_test_file = self._find_matching_test(symbol_name, file_path, existing_test_catalog)
            has_coverage = matching_test_file is not None

            # Trace impacted APIs and services via Code Knowledge Graph
            impacted_endpoints, impacted_services = self._trace_impacted_graph(symbol_name, file_path)
            if is_endpoint and symbol_name not in impacted_endpoints:
                impacted_endpoints.append(f"{file_path}:{symbol_name}")

            # Generate scenarios across categories
            scenarios_for_symbol = self._build_scenarios_for_symbol(
                target_file=file_path,
                target_symbol=symbol_name,
                symbol_type=symbol_type,
                signature=signature,
                is_endpoint=is_endpoint,
                matching_test_file=matching_test_file,
                has_coverage=has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
            )
            generated_scenarios.extend(scenarios_for_symbol)

        # 5. Persist scenarios
        self.db.add_all(generated_scenarios)
        self.db.commit()

        for sc in generated_scenarios:
            self.db.refresh(sc)

        logger.info(
            "Test Intelligence: generated %d scenarios across %d modified symbols for repo %d",
            len(generated_scenarios),
            len(modified_symbols),
            self.repository_id,
        )
        return generated_scenarios

    def _extract_modified_symbols(
        self, diff: str, diff_hunks_by_file: Dict[str, List[PRDiffHunk]]
    ) -> List[Dict[str, Any]]:
        """
        Extracts modified functions and methods using fine-grained AST inspection.
        """
        symbols = []
        seen = set()

        # Re-use impact change detector
        detected = detect_code_changes(diff)
        for cs in detected.changed_symbols:
            key = (cs.file_path, cs.symbol_name)
            if key not in seen:
                seen.add(key)
                is_endpoint = (
                    cs.symbol_type == "api_endpoint"
                    or "route" in cs.file_path.lower()
                    or "api" in cs.file_path.lower()
                )
                sig = f"{cs.symbol_type} {cs.symbol_name}"
                if cs.symbol_type in ("function", "method"):
                    sig = f"def {cs.symbol_name}()"
                elif cs.symbol_type == "class":
                    sig = f"class {cs.symbol_name}"

                symbols.append({
                    "file_path": cs.file_path,
                    "name": cs.symbol_name,
                    "type": cs.symbol_type,
                    "signature": sig,
                    "is_endpoint": is_endpoint,
                })

        # Also inspect diff hunks for additional function definitions added or changed
        func_re_py = re.compile(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\):")
        func_re_js = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)")
        const_fn_re = re.compile(r"^\s*(?:export\s+)?const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>")

        for file_path, hunks in diff_hunks_by_file.items():
            if "test" in file_path.lower():
                continue
            for hunk in hunks:
                for line in hunk.lines:
                    if line.startswith("+"):
                        cleaned = line[1:].strip()
                        m_py = func_re_py.match(cleaned)
                        if m_py:
                            name = m_py.group(1)
                            key = (file_path, name)
                            if key not in seen:
                                seen.add(key)
                                symbols.append({
                                    "file_path": file_path,
                                    "name": name,
                                    "type": "function",
                                    "signature": f"def {name}({m_py.group(2)})",
                                    "is_endpoint": "route" in file_path.lower() or "api" in file_path.lower(),
                                })
                            continue

                        m_js = func_re_js.match(cleaned) or const_fn_re.match(cleaned)
                        if m_js:
                            name = m_js.group(1)
                            key = (file_path, name)
                            if key not in seen:
                                seen.add(key)
                                symbols.append({
                                    "file_path": file_path,
                                    "name": name,
                                    "type": "function",
                                    "signature": f"{name}({m_js.group(2)})",
                                    "is_endpoint": "route" in file_path.lower() or "api" in file_path.lower(),
                                })

        # Fallback if diff only altered lines inside existing files without new signature headers
        if not symbols and diff_hunks_by_file:
            for file_path in diff_hunks_by_file.keys():
                if "test" not in file_path.lower():
                    basename = file_path.split("/")[-1].split(".")[0]
                    symbols.append({
                        "file_path": file_path,
                        "name": basename,
                        "type": "module",
                        "signature": f"module {basename}",
                        "is_endpoint": "route" in file_path.lower() or "api" in file_path.lower(),
                    })
        return symbols

    def _discover_existing_tests(self) -> List[Dict[str, Any]]:
        """
        Discovers existing test files in the repository and inspects their target symbols.
        """
        test_docs = self.db.execute(
            select(Document).where(
                Document.repository_id == self.repository_id,
                (Document.path.ilike("%test%") | Document.path.ilike("%spec%")),
            )
        ).scalars().all()

        catalog = []
        for doc in test_docs:
            path = doc.path.replace("\\", "/")
            framework = "pytest" if path.endswith(".py") else "vitest"
            tested_symbols = []

            # Extract tested names from file name convention
            base = path.split("/")[-1]
            for ext in [".test.jsx", ".test.js", ".test.tsx", ".test.ts", ".py"]:
                if base.endswith(ext):
                    clean = base[:-len(ext)].replace("test_", "").replace("_test", "")
                    tested_symbols.append(clean)
                    break

            catalog.append({
                "test_file": path,
                "framework": framework,
                "tested_symbols": tested_symbols,
            })
        return catalog

    def _find_matching_test(
        self, symbol_name: str, file_path: str, catalog: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Matches a modified symbol to an existing test file.
        """
        file_base = file_path.split("/")[-1].split(".")[0]
        sym_lower = symbol_name.lower()
        file_base_lower = file_base.lower()

        for entry in catalog:
            tfile = entry["test_file"].lower()
            if f"test_{file_base_lower}" in tfile or f"{file_base_lower}.test" in tfile or f"{file_base_lower}_test" in tfile:
                return entry["test_file"]
            if any(sym_lower in s.lower() for s in entry.get("tested_symbols", [])):
                return entry["test_file"]
        return None

    def _trace_impacted_graph(self, symbol_name: str, file_path: str) -> Tuple[List[str], List[str]]:
        """
        Queries Code Knowledge Graph for callers, dependent services, and API endpoints.
        """
        impacted_endpoints = []
        impacted_services = []

        # Find node in graph
        node = self.db.execute(
            select(CodeGraphNode).where(
                CodeGraphNode.repository_id == self.repository_id,
                CodeGraphNode.file_path == file_path,
                CodeGraphNode.name == symbol_name,
            )
        ).scalar_one_or_none()

        if not node:
            # Fallback: find node by name only in repo
            node = self.db.execute(
                select(CodeGraphNode).where(
                    CodeGraphNode.repository_id == self.repository_id,
                    CodeGraphNode.name == symbol_name,
                )
            ).scalar_one_or_none()

        if node:
            # Reverse traverse incoming edges (callers, references, imports)
            edges = self.db.execute(
                select(CodeGraphEdge).where(
                    CodeGraphEdge.repository_id == self.repository_id,
                    CodeGraphEdge.target_node_id == node.id,
                )
            ).scalars().all()

            source_ids = [e.source_node_id for e in edges]
            if source_ids:
                source_nodes = self.db.execute(
                    select(CodeGraphNode).where(CodeGraphNode.id.in_(source_ids))
                ).scalars().all()

                for sn in source_nodes:
                    if sn.node_type == "api_endpoint" or "route" in sn.file_path.lower():
                        impacted_endpoints.append(f"{sn.file_path}:{sn.name}")
                    else:
                        impacted_services.append(f"{sn.file_path}:{sn.name}")

        return list(set(impacted_endpoints)), list(set(impacted_services))

    def _build_scenarios_for_symbol(
        self,
        target_file: str,
        target_symbol: str,
        symbol_type: str,
        signature: str,
        is_endpoint: bool,
        matching_test_file: Optional[str],
        has_coverage: bool,
        impacted_endpoints: List[str],
        impacted_services: List[str],
        pull_request_id: Optional[int],
        review_run_id: Optional[int],
    ) -> List[TestScenario]:
        """
        Builds 8 structured test scenarios covering all required categories.
        """
        scenarios = []

        # Canonical test file recommendation
        ext = ".py" if target_file.endswith(".py") else ".jsx" if target_file.endswith(".jsx") else ".ts"
        base_name = target_file.split("/")[-1].split(".")[0]
        suggested_test_file = (
            matching_test_file
            if matching_test_file
            else f"backend/tests/test_{base_name}.py" if ext == ".py" else f"frontend/tests/{base_name}.test{ext}"
        )

        # 1. Positive Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="positive",
                title=f"Verify happy-path execution of '{target_symbol}'",
                description=f"Validate that '{target_symbol}' executes successfully with nominal, valid inputs and produces expected return structures.",
                edge_case_notes="Ensure all required parameters are provided with typical real-world values.",
                suggested_assertions=[
                    f"Result of {target_symbol} is not None",
                    "Return status / structure matches expected schema",
                    "Persisted state reflects intended modification",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="high",
            )
        )

        # 2. Negative Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="negative",
                title=f"Verify error handling for invalid inputs in '{target_symbol}'",
                description=f"Ensure '{target_symbol}' safely catches malformed parameters or nonexistent entity IDs without crashing.",
                edge_case_notes="Pass non-existent IDs, invalid enum values, or missing foreign keys.",
                suggested_assertions=[
                    "Raises appropriate HTTPException or ValueError",
                    "Returns descriptive client error message",
                    "No partial database commits occur on failure",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="high",
            )
        )

        # 3. Boundary Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="boundary",
                title=f"Verify boundary limit values for '{target_symbol}'",
                description=f"Check behavior of '{target_symbol}' with empty strings, 0, maximum string lengths, and empty collections.",
                edge_case_notes="Test empty list [], zero integer (0), and max length payloads (e.g. 1024+ chars).",
                suggested_assertions=[
                    "Handles empty collection gracefully without IndexError",
                    "Correctly clamps or validates upper boundary constraints",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="medium",
            )
        )

        # 4. Validation Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="validation",
                title=f"Verify schema & parameter validation on '{target_symbol}'",
                description=f"Enforce that input DTOs and type constraints reject invalid data types and missing required fields.",
                edge_case_notes="Pass wrong data types (e.g. string for integer, null for non-nullable).",
                suggested_assertions=[
                    "Pydantic / input validator rejects payload with HTTP 422 Unprocessable Entity",
                    "Error details point to exact violating field",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="medium",
            )
        )

        # 5. Authentication Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="authentication",
                title=f"Verify authentication enforcement for '{target_symbol}'",
                description=f"Ensure unauthenticated requests or expired credentials fail with HTTP 401 Unauthorized.",
                edge_case_notes="Test with omitted auth header, expired JWT cookie, and forged signature.",
                suggested_assertions=[
                    "HTTP status code is strictly 401 Unauthorized",
                    "Sensitive logic is not executed prior to auth verification",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="critical" if is_endpoint else "low",
            )
        )

        # 6. Authorization Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="authorization",
                title=f"Verify RBAC & multi-tenant isolation for '{target_symbol}'",
                description=f"Verify that users without required permissions (or belonging to another organization) are rejected with HTTP 403 / 404.",
                edge_case_notes="Test access across Organization A vs Organization B, and developer role attempting admin actions.",
                suggested_assertions=[
                    "HTTP status code is 403 Forbidden or 404 Not Found",
                    "Cross-tenant data cannot be leaked or updated",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="critical" if is_endpoint else "medium",
            )
        )

        # 7. Integration Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="integration",
                title=f"Verify end-to-end integration flow involving '{target_symbol}'",
                description=f"Trace integration from API entry point through database transaction and vector retrieval.",
                edge_case_notes="Simulate complete lifecycle with DB commit and verify database query integrity.",
                suggested_assertions=[
                    "Transaction commits successfully without foreign key violation",
                    "Dependent services receive valid response payload",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="high",
            )
        )

        # 8. Regression Case
        scenarios.append(
            TestScenario(
                repository_id=self.repository_id,
                pull_request_id=pull_request_id,
                review_run_id=review_run_id,
                target_file=target_file,
                target_symbol=target_symbol,
                category="regression",
                title=f"Verify existing callers of '{target_symbol}' remain unbroken",
                description=f"Run regression checks against all downstream components: {', '.join(impacted_services[:3]) or 'existing callers'}.",
                edge_case_notes="Verify backward compatibility of parameters and response attributes.",
                suggested_assertions=[
                    "Existing callers invoke function with legacy arguments without TypeError",
                    "Return dictionary or model contains all backward-compatible keys",
                ],
                existing_test_file=suggested_test_file,
                coverage_gap=not has_coverage,
                impacted_endpoints=impacted_endpoints,
                impacted_services=impacted_services,
                priority="high" if impacted_services else "medium",
            )
        )

        return scenarios


def run_test_intelligence_analysis(
    db: Session,
    repository_id: int,
    diff: str,
    pull_request_id: Optional[int] = None,
    review_run_id: Optional[int] = None,
) -> List[TestScenario]:
    """
    Entry point function for orchestrating AI Test Intelligence analysis.
    """
    analyzer = TestIntelligenceAnalyzer(db=db, repository_id=repository_id)
    return analyzer.analyze(
        diff=diff,
        pull_request_id=pull_request_id,
        review_run_id=review_run_id,
    )
