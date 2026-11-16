"""
PR Analysis & Knowledge Graph Context Extractor — RepoMind 2.0.

Extracts structured PR information:
  - Title, description, commit SHAs, source/target branches
  - Changed files, additions, deletions, file status (added/modified/deleted)
  - Detailed diff hunks for precise line-level evidence grounding
  - Architectural relationships via Code Knowledge Graph (related modules,
    dependent subsystems, affected API endpoints, and database models)
"""
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

from backend.app.github.models import PullRequest
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge

logger = logging.getLogger(__name__)


@dataclass
class PRDiffHunk:
    """Represents a unified diff hunk (@@ -l,s +l,s @@) for evidence verification."""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str] = field(default_factory=list)
    added_line_numbers: Set[int] = field(default_factory=set)


@dataclass
class PRFileSummary:
    """Summary of a changed file within the PR."""
    path: str
    status: str  # added | modified | deleted | renamed
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None


@dataclass
class PRAnalysisContext:
    """
    Complete repository-aware PR analysis context.
    Supplies architectural grounding to review prompts, conflict detection,
    and risk engines.
    """
    pr_id: int
    repository_id: int
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    base_sha: str
    head_sha: str
    additions: int
    deletions: int
    changed_files: List[str]
    files_summary: List[PRFileSummary]
    diff_hunks_by_file: Dict[str, List[PRDiffHunk]] = field(default_factory=dict)
    related_modules: List[str] = field(default_factory=list)
    dependent_modules: List[str] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    affected_models: List[str] = field(default_factory=list)
    has_empty_diff: bool = False
    has_only_deletions: bool = False


_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_diff_hunks(diff: str) -> Dict[str, List[PRDiffHunk]]:
    """
    Parse a unified git diff into structured hunks per file path.
    Maps new revision line numbers for precise grounding checks.
    """
    hunks_by_file: Dict[str, List[PRDiffHunk]] = {}
    current_file: Optional[str] = None
    current_hunk: Optional[PRDiffHunk] = None
    new_line_cursor = 0

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            if current_file not in hunks_by_file:
                hunks_by_file[current_file] = []
            current_hunk = None
            continue
        elif line.startswith("+++ /dev/null"):
            # File deleted
            current_hunk = None
            continue

        if line.startswith("@@ ") and current_file:
            match = _HUNK_HEADER_RE.match(line)
            if match:
                old_start = int(match.group(1))
                old_lines = int(match.group(2) or 1)
                new_start = int(match.group(3))
                new_lines = int(match.group(4) or 1)
                current_hunk = PRDiffHunk(
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                )
                hunks_by_file[current_file].append(current_hunk)
                new_line_cursor = new_start
            continue

        if current_hunk is not None:
            current_hunk.lines.append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.added_line_numbers.add(new_line_cursor)
                new_line_cursor += 1
            elif line.startswith("-") and not line.startswith("---"):
                pass  # deleted line in old revision
            else:
                # context line
                new_line_cursor += 1

    return hunks_by_file


def query_related_modules(
    db: Session,
    repository_id: int,
    changed_files: List[str],
) -> Dict[str, List[str]]:
    """
    Query the persistent Code Knowledge Graph to extract:
    - Related parent modules
    - Dependent modules that import or call the changed files
    - Exposed API endpoints affected by the changes
    - Database models affected by the changes
    """
    if not changed_files:
        return {
            "related_modules": [],
            "dependent_modules": [],
            "affected_endpoints": [],
            "affected_models": [],
        }

    # Normalize paths
    normalized_paths = [f.replace("\\", "/").lstrip("/") for f in changed_files]

    # Find file nodes
    file_nodes = (
        db.query(CodeGraphNode)
        .filter(
            CodeGraphNode.repository_id == repository_id,
            CodeGraphNode.file_path.in_(normalized_paths),
        )
        .all()
    )

    if not file_nodes:
        # Fallback: derive simple module directories from paths
        modules = sorted(list(set(
            "/".join(p.split("/")[:-1]) for p in normalized_paths if "/" in p
        )))
        return {
            "related_modules": modules,
            "dependent_modules": [],
            "affected_endpoints": [],
            "affected_models": [],
        }

    file_node_ids = [n.id for n in file_nodes]

    # 1. Parent modules containing these files
    parent_edges = (
        db.query(CodeGraphEdge, CodeGraphNode)
        .join(CodeGraphNode, CodeGraphEdge.source_node_id == CodeGraphNode.id)
        .filter(
            CodeGraphEdge.repository_id == repository_id,
            CodeGraphEdge.target_node_id.in_(file_node_ids),
            CodeGraphEdge.relation_type == "contains",
            CodeGraphNode.node_type == "module",
        )
        .all()
    )
    related_modules = sorted(list(set(n.name for _, n in parent_edges)))

    # Fallback if no module nodes exist in DB
    if not related_modules:
        related_modules = sorted(list(set(
            "/".join(p.split("/")[:-1]) for p in normalized_paths if "/" in p
        )))

    # 2. Dependent modules/files importing or calling these files
    dependent_edges = (
        db.query(CodeGraphEdge, CodeGraphNode)
        .join(CodeGraphNode, CodeGraphEdge.source_node_id == CodeGraphNode.id)
        .filter(
            CodeGraphEdge.repository_id == repository_id,
            CodeGraphEdge.target_node_id.in_(file_node_ids),
            CodeGraphEdge.relation_type.in_(["imports", "calls", "depends_on"]),
        )
        .all()
    )
    dependent_modules = sorted(list(set(
        n.file_path for _, n in dependent_edges if n.file_path not in normalized_paths
    )))

    # 3. Affected API endpoints and Database models within these files
    child_symbols = (
        db.query(CodeGraphEdge, CodeGraphNode)
        .join(CodeGraphNode, CodeGraphEdge.target_node_id == CodeGraphNode.id)
        .filter(
            CodeGraphEdge.repository_id == repository_id,
            CodeGraphEdge.source_node_id.in_(file_node_ids),
            CodeGraphEdge.relation_type == "contains",
            CodeGraphNode.node_type.in_(["api_endpoint", "db_model"]),
        )
        .all()
    )

    affected_endpoints = sorted(list(set(
        n.name for _, n in child_symbols if n.node_type == "api_endpoint"
    )))
    affected_models = sorted(list(set(
        n.name for _, n in child_symbols if n.node_type == "db_model"
    )))

    return {
        "related_modules": related_modules,
        "dependent_modules": dependent_modules[:15],
        "affected_endpoints": affected_endpoints,
        "affected_models": affected_models,
    }


def extract_pr_analysis_context(
    db: Session,
    pr: PullRequest,
    diff: str,
    pr_files_raw: Optional[List[dict]] = None,
) -> PRAnalysisContext:
    """
    Extract and assemble the complete PRAnalysisContext.
    """
    pr_files_raw = pr_files_raw or []
    files_summary: List[PRFileSummary] = []
    changed_files: List[str] = []

    total_additions = 0
    total_deletions = 0

    for f in pr_files_raw:
        filename = f.get("filename", "")
        if not filename:
            continue
        changed_files.append(filename)
        add = f.get("additions", 0)
        del_ = f.get("deletions", 0)
        total_additions += add
        total_deletions += del_
        files_summary.append(
            PRFileSummary(
                path=filename,
                status=f.get("status", "modified"),
                additions=add,
                deletions=del_,
                patch=f.get("patch"),
            )
        )

    # If pr_files_raw was empty, extract paths from diff headers
    if not changed_files and diff:
        diff_paths = re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)
        for p in diff_paths:
            if p not in changed_files and p != "/dev/null":
                changed_files.append(p)
                files_summary.append(
                    PRFileSummary(path=p, status="modified")
                )

    # Parse hunks for evidence grounding
    diff_hunks = parse_diff_hunks(diff) if diff else {}

    # Query Code Knowledge Graph for architectural context
    kg_context = query_related_modules(db, pr.repository_id, changed_files)

    has_empty = not diff or not diff.strip() or len(changed_files) == 0
    only_deletions = (
        not has_empty
        and total_deletions > 0
        and total_additions == 0
        and all(f.status == "deleted" for f in files_summary if f.status)
    )

    return PRAnalysisContext(
        pr_id=pr.id,
        repository_id=pr.repository_id,
        title=pr.title or "",
        description=pr.description or "",
        author=pr.github_author_login or "unknown",
        source_branch=pr.source_branch or "unknown",
        target_branch=pr.target_branch or "main",
        base_sha=pr.base_sha or "",
        head_sha=pr.head_sha or "",
        additions=total_additions or (pr.additions or 0),
        deletions=total_deletions or (pr.deletions or 0),
        changed_files=changed_files,
        files_summary=files_summary,
        diff_hunks_by_file=diff_hunks,
        related_modules=kg_context["related_modules"],
        dependent_modules=kg_context["dependent_modules"],
        affected_endpoints=kg_context["affected_endpoints"],
        affected_models=kg_context["affected_models"],
        has_empty_diff=has_empty,
        has_only_deletions=only_deletions,
    )
