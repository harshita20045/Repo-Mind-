"""
Query Classifier and Entity Extractor for RepoMind AI Assistant.

Categorizes developer questions into supported repository intelligence categories
and extracts referenced entities (symbols, files, endpoints, PR numbers).
"""
import re
from enum import Enum
from typing import List, Optional, Set
from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    MODULE_EXPLANATION = "module_explanation"
    AUTH_FLOW = "auth_flow"
    API_IMPLEMENTATION = "api_implementation"
    DB_ACCESS = "db_access"
    PR_REVIEW_RATIONALE = "pr_review_rationale"
    DEPENDENCY_GRAPH = "dependency_graph"
    ENDPOINT_LIFECYCLE = "endpoint_lifecycle"
    TEST_COVERAGE = "test_coverage"
    HISTORICAL_DECISION = "historical_decision"
    GENERAL_CODE_SEARCH = "general_code_search"


class ExtractedEntities(BaseModel):
    intent: QueryIntent
    symbols: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    pr_id: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)


def extract_files(text: str) -> List[str]:
    """Extract filenames and file paths (e.g., service.py, /app/auth/models.py)."""
    file_pattern = r'\b[\w\-\./]+\.(?:py|jsx?|tsx?|json|ya?ml|sql|html|css|md)\b'
    matches = re.findall(file_pattern, text, re.IGNORECASE)
    # Filter out pure extensions or duplicates
    seen = set()
    files = []
    for m in matches:
        clean = m.strip(" ./'\"")
        if clean and clean not in seen:
            seen.add(clean)
            files.append(clean)
    return files


def extract_endpoints(text: str) -> List[str]:
    """Extract API endpoints (e.g. GET /users, /api/v1/auth/login, POST /chat/sessions)."""
    endpoint_pattern = r'(?:(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+)?(/[\w\-/{}]+)'
    matches = re.findall(endpoint_pattern, text)
    endpoints = []
    seen = set()
    for m in matches:
        if m != "/" and m not in seen and not m.endswith(".py") and not m.endswith(".js"):
            seen.add(m)
            endpoints.append(m)
    return endpoints


def extract_symbols(text: str) -> List[str]:
    """Extract candidate function, class, or variable names (e.g., `send_message`, User, `RAGRetriever`)."""
    # 1. Backtick enclosed symbols: `create_session`
    backtick_matches = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_]*)`', text)
    
    # 2. Function calls like send_message() or create_session()
    call_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\(\)', text)
    
    # 3. CamelCase or snake_case words (excluding common English stopwords)
    word_matches = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b', text)
    stopwords = {
        "what", "where", "which", "when", "why", "how", "does", "this", "that", "these",
        "those", "there", "their", "have", "with", "from", "into", "explain", "called",
        "module", "function", "class", "method", "endpoint", "service", "database",
        "work", "flagged", "depend", "depends", "happens", "cover", "tests", "coverage",
        "about", "repository", "codebase", "implementation", "accesses", "accessed"
    }
    
    candidates = []
    seen = set()
    for s in backtick_matches + call_matches:
        if s.lower() not in stopwords and s not in seen:
            seen.add(s)
            candidates.append(s)
            
    for w in word_matches:
        if ("_" in w or (w[0].isupper() and any(c.islower() for c in w))) and w.lower() not in stopwords and w not in seen:
            seen.add(w)
            candidates.append(w)
            
    return candidates


def extract_pr_id(text: str) -> Optional[int]:
    """Extract referenced PR number (e.g. PR #42, PR 42, #42)."""
    match = re.search(r'\b(?:pr|pull\s*request)?\s*#?([0-9]+)\b', text, re.IGNORECASE)
    if match and ("pr" in text.lower() or "pull request" in text.lower() or "#" in text):
        try:
            return int(match.group(1))
        except (ValueError, IndexError):
            return None
    return None


def classify_query(text: str, context_type: str = "repository", context_id: Optional[int] = None) -> ExtractedEntities:
    """
    Classifies user question into one of the 8 supported categories + general search,
    and extracts referenced entities.
    """
    normalized = text.lower().strip()
    files = extract_files(text)
    endpoints = extract_endpoints(text)
    symbols = extract_symbols(text)
    pr_id = extract_pr_id(text)
    
    if context_type in ("pr", "pull_request") and context_id and not pr_id:
        pr_id = context_id

    # 1. PR Review Rationale ("Why was this PR flagged?", review findings, flags)
    if (
        "flagged" in normalized
        or "review finding" in normalized
        or "why did the review" in normalized
        or "why was this pr" in normalized
        or "pr violations" in normalized
        or (context_type in ("pr", "pull_request") and ("flag" in normalized or "violation" in normalized or "failing" in normalized))
    ):
        return ExtractedEntities(
            intent=QueryIntent.PR_REVIEW_RATIONALE,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 2. Authentication Flow ("How does authentication work?", login, tokens, rbac)
    if (
        "how does auth" in normalized
        or "authentication work" in normalized
        or "authorization work" in normalized
        or "login flow" in normalized
        or "jwt token" in normalized
        or "how do permissions work" in normalized
        or "rbac work" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.AUTH_FLOW,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 3. Database Access ("Which service accesses this database?", models, tables, orm)
    if (
        "accesses this database" in normalized
        or "access this database" in normalized
        or "accesses the database" in normalized
        or "which service accesses" in normalized
        or "queries this table" in normalized
        or "database interaction" in normalized
        or "which models" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.DB_ACCESS,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 4. Dependency Graph / Callers ("Which modules depend on this function?", who calls X)
    if (
        "depend on this function" in normalized
        or "modules depend on" in normalized
        or "who calls" in normalized
        or "what calls" in normalized
        or "caller of" in normalized
        or "callers of" in normalized
        or "depend on" in normalized and ("function" in normalized or "module" in normalized or bool(symbols))
    ):
        return ExtractedEntities(
            intent=QueryIntent.DEPENDENCY_GRAPH,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 5. Endpoint Lifecycle ("What happens when this endpoint is called?", request flow)
    if (
        ("what happens when" in normalized and ("endpoint" in normalized or "called" in normalized or "/" in normalized))
        or "request lifecycle" in normalized
        or "execution flow of endpoint" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.ENDPOINT_LIFECYCLE,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 6. API Implementation ("Where is this API implemented?", find endpoint)
    if (
        "where is this api" in normalized
        or "where is the api" in normalized
        or "api implemented" in normalized
        or "endpoint implemented" in normalized
        or "where is route" in normalized
        or bool(endpoints) and ("where" in normalized or "how" in normalized or "implemented" in normalized)
    ):
        return ExtractedEntities(
            intent=QueryIntent.API_IMPLEMENTATION,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 7. Test Coverage ("Which tests cover this functionality?", test cases, scenarios)
    if (
        "which tests cover" in normalized
        or "tests cover" in normalized
        or "test coverage for" in normalized
        or "what tests exist for" in normalized
        or "test scenarios for" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.TEST_COVERAGE,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 8. Module Explanation ("Explain this module", "What does module X do?", overview)
    if (
        "explain this module" in normalized
        or "explain module" in normalized
        or "what does this module" in normalized
        or "architecture of" in normalized
        or "how is the project structured" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.MODULE_EXPLANATION,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # 9. Historical Decisions & Bug History ("Why was this module refactored?", ADRs, past bugs)
    if (
        "why was" in normalized
        or "refactor" in normalized
        or "decision" in normalized
        or "adr" in normalized
        or "historical" in normalized
        or "bug before" in normalized
        or "similar bug" in normalized
        or "schema change" in normalized
        or "past change" in normalized
        or "engineering decision" in normalized
        or "who changed" in normalized
        or "when was" in normalized
    ):
        return ExtractedEntities(
            intent=QueryIntent.HISTORICAL_DECISION,
            symbols=symbols,
            files=files,
            endpoints=endpoints,
            pr_id=pr_id,
        )

    # Default: General code search
    return ExtractedEntities(
        intent=QueryIntent.GENERAL_CODE_SEARCH,
        symbols=symbols,
        files=files,
        endpoints=endpoints,
        pr_id=pr_id,
    )

