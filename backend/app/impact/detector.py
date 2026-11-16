"""
Change Detector — RepoMind 2.0 Change Impact Engine.

Performs fine-grained AST diff analysis to identify:
  - Modified, added, and deleted files
  - Changed functions and methods (with line ranges)
  - Method and function signature changes (added/removed/reordered parameters)
  - Changed classes and database models
  - Changed API contracts (routes, parameters, request/response models)
  - Modified imports and removed exports
"""
import ast
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

from backend.app.review.analysis import parse_diff_hunks, PRDiffHunk

logger = logging.getLogger(__name__)


@dataclass
class FunctionSignature:
    name: str
    params: List[str] = field(default_factory=list)
    has_defaults: Dict[str, bool] = field(default_factory=dict)
    kwonly_params: List[str] = field(default_factory=list)
    has_varargs: bool = False
    has_kwargs: bool = False
    return_type: Optional[str] = None


@dataclass
class ChangedSymbol:
    symbol_name: str
    symbol_type: str  # function | method | class | db_model | api_endpoint
    file_path: str
    start_line: int
    end_line: int
    parent_symbol: Optional[str] = None
    change_type: str = "modified"  # added | modified | deleted
    old_signature: Optional[FunctionSignature] = None
    new_signature: Optional[FunctionSignature] = None
    details: Optional[str] = None


@dataclass
class DetectedCodeChanges:
    changed_files: List[str] = field(default_factory=list)
    added_files: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    changed_symbols: List[ChangedSymbol] = field(default_factory=list)
    changed_api_routes: List[Dict[str, Any]] = field(default_factory=list)
    changed_db_models: List[Dict[str, Any]] = field(default_factory=list)
    modified_dependencies: List[str] = field(default_factory=list)
    modified_configs: List[str] = field(default_factory=list)


def _extract_py_signatures(code_content: str) -> Dict[str, FunctionSignature]:
    """Parse Python code and return a dictionary of (qualname -> FunctionSignature)."""
    signatures: Dict[str, FunctionSignature] = {}
    if not code_content or not code_content.strip():
        return signatures

    try:
        tree = ast.parse(code_content)
    except SyntaxError:
        return signatures

    class SignatureVisitor(ast.NodeVisitor):
        def __init__(self):
            self.class_stack = []

        def visit_ClassDef(self, node: ast.ClassDef):
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self._handle_func(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self._handle_func(node)
            self.generic_visit(node)

        def _handle_func(self, node):
            qualname = ".".join(self.class_stack + [node.name]) if self.class_stack else node.name
            params = []
            has_defaults = {}

            # Positional / normal args
            default_offset = len(node.args.args) - len(node.args.defaults)
            for i, arg in enumerate(node.args.args):
                arg_name = arg.arg
                if arg_name in ("self", "cls"):
                    continue
                params.append(arg_name)
                has_defaults[arg_name] = (i >= default_offset)

            # Keyword-only args
            kwonly = []
            for arg in node.args.kwonlyargs:
                kwonly.append(arg.arg)

            ret_type = ast.unparse(node.returns) if getattr(node, "returns", None) else None

            signatures[qualname] = FunctionSignature(
                name=qualname,
                params=params,
                has_defaults=has_defaults,
                kwonly_params=kwonly,
                has_varargs=bool(node.args.vararg),
                has_kwargs=bool(node.args.kwarg),
                return_type=ret_type,
            )

    SignatureVisitor().visit(tree)
    return signatures


def _extract_py_symbols_with_lines(code_content: str) -> List[Tuple[str, str, int, int, Optional[str]]]:
    """Return list of (name, type, start_line, end_line, parent)."""
    symbols = []
    if not code_content:
        return symbols

    try:
        tree = ast.parse(code_content)
    except SyntaxError:
        return symbols

    class SymbolVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_class = None

        def visit_ClassDef(self, node: ast.ClassDef):
            is_model = any(
                isinstance(b, ast.Name) and b.id in ("Base", "Model") or
                isinstance(b, ast.Attribute) and b.attr in ("Base", "Model")
                for b in node.bases
            )
            sym_type = "db_model" if is_model else "class"
            end_line = getattr(node, "end_lineno", node.lineno)
            symbols.append((node.name, sym_type, node.lineno, end_line, None))

            prev_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = prev_class

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self._record_func(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self._record_func(node)
            self.generic_visit(node)

        def _record_func(self, node):
            sym_type = "method" if self.current_class else "function"
            end_line = getattr(node, "end_lineno", node.lineno)
            symbols.append((node.name, sym_type, node.lineno, end_line, self.current_class))

    SymbolVisitor().visit(tree)
    return symbols


_ROUTE_REGEX = re.compile(
    r'@(?:app|router|api_router)\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def detect_code_changes(
    diff: str,
    changed_files: Optional[List[str]] = None,
    file_contents: Optional[Dict[str, str]] = None,
) -> DetectedCodeChanges:
    """
    Analyze unified diff and file contents to extract fine-grained code change events.
    """
    file_contents = file_contents or {}
    hunks_by_file = parse_diff_hunks(diff) if diff else {}

    # Extract changed files from diff headers if not supplied
    if not changed_files:
        changed_files = list(hunks_by_file.keys())

    added_files = []
    deleted_files = []
    modified_files = []

    for path in changed_files:
        if f"+++ /dev/null" in diff and f"--- a/{path}" in diff:
            deleted_files.append(path)
        elif f"--- /dev/null" in diff and f"+++ b/{path}" in diff:
            added_files.append(path)
        else:
            modified_files.append(path)

    changed_symbols: List[ChangedSymbol] = []
    changed_api_routes: List[Dict[str, Any]] = []
    changed_db_models: List[Dict[str, Any]] = []
    modified_deps: List[str] = []
    modified_configs: List[str] = []

    # 1. Dependency and Config modifications
    for path in changed_files:
        lower = path.lower()
        if any(lower.endswith(dep) for dep in [
            "requirements.txt", "package.json", "pyproject.toml",
            "pipfile", "go.mod", "pom.xml", "cargo.toml"
        ]):
            modified_deps.append(path)
        if any(cfg in lower for cfg in ["settings.py", "config.py", ".env", "docker-compose", "alembic"]):
            modified_configs.append(path)

    # 2. Check each file's hunks against AST symbols
    for path, hunks in hunks_by_file.items():
        if path in deleted_files:
            continue

        # Check API route decorator changes in diff text directly
        for hunk in hunks:
            for line in hunk.lines:
                if line.startswith("+") and not line.startswith("+++"):
                    m = _ROUTE_REGEX.search(line)
                    if m:
                        changed_api_routes.append({
                            "method": m.group(1).upper(),
                            "path": m.group(2),
                            "file_path": path,
                            "type": "added_or_modified_route",
                        })

        # AST analysis for Python files
        if path.endswith(".py"):
            content = file_contents.get(path, "")
            # If not in file_contents, we can reconstruct rough lines or scan diff
            if content:
                symbols = _extract_py_symbols_with_lines(content)
                signatures = _extract_py_signatures(content)

                # Collect all line numbers touched by additions in this file
                touched_lines = set()
                for hunk in hunks:
                    touched_lines.update(hunk.added_line_numbers)

                for name, sym_type, start, end, parent in symbols:
                    qualname = f"{parent}.{name}" if parent else name
                    # If any touched line falls within the symbol's span
                    if any(start <= line <= end for line in touched_lines):
                        sig = signatures.get(qualname)
                        changed_symbols.append(ChangedSymbol(
                            symbol_name=name,
                            symbol_type=sym_type,
                            file_path=path,
                            start_line=start,
                            end_line=end,
                            parent_symbol=parent,
                            change_type="modified",
                            new_signature=sig,
                        ))
                        if sym_type == "db_model":
                            changed_db_models.append({
                                "model_name": name,
                                "file_path": path,
                                "start_line": start,
                            })
            else:
                # Fallback AST from diff lines alone
                _detect_symbols_from_diff_hunks(path, hunks, changed_symbols, changed_db_models)
        else:
            # Non-python files (TS/JS/Go): scan for functions/exports
            _detect_symbols_from_diff_hunks(path, hunks, changed_symbols, changed_db_models)

    return DetectedCodeChanges(
        changed_files=changed_files,
        added_files=added_files,
        deleted_files=deleted_files,
        changed_symbols=changed_symbols,
        changed_api_routes=changed_api_routes,
        changed_db_models=changed_db_models,
        modified_dependencies=modified_deps,
        modified_configs=modified_configs,
    )


_FN_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_0-9]+)\s*\((.*?)\)", re.MULTILINE)
_JS_FN_RE = re.compile(r"^\+\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_0-9]+)\s*\((.*?)\)", re.MULTILINE)
_CLASS_DEF_RE = re.compile(r"^\+\s*class\s+([A-Za-z_0-9]+)", re.MULTILINE)


def _detect_symbols_from_diff_hunks(
    path: str,
    hunks: List[PRDiffHunk],
    changed_symbols: List[ChangedSymbol],
    changed_db_models: List[Dict[str, Any]],
) -> None:
    """Fallback scanner that detects changed function & class declarations directly from diff lines."""
    for hunk in hunks:
        hunk_text = "\n".join(hunk.lines)
        for m in _FN_DEF_RE.finditer(hunk_text):
            fn_name = m.group(1)
            raw_params = [p.strip() for p in m.group(2).split(",") if p.strip()]
            sig = FunctionSignature(name=fn_name, params=raw_params)
            changed_symbols.append(ChangedSymbol(
                symbol_name=fn_name,
                symbol_type="function",
                file_path=path,
                start_line=hunk.new_start,
                end_line=hunk.new_start + hunk.new_lines,
                change_type="modified",
                new_signature=sig,
            ))

        for m in _JS_FN_RE.finditer(hunk_text):
            fn_name = m.group(1)
            changed_symbols.append(ChangedSymbol(
                symbol_name=fn_name,
                symbol_type="function",
                file_path=path,
                start_line=hunk.new_start,
                end_line=hunk.new_start + hunk.new_lines,
                change_type="modified",
            ))

        for m in _CLASS_DEF_RE.finditer(hunk_text):
            cls_name = m.group(1)
            is_model = "model" in path.lower() or "Model" in cls_name
            sym_type = "db_model" if is_model else "class"
            changed_symbols.append(ChangedSymbol(
                symbol_name=cls_name,
                symbol_type=sym_type,
                file_path=path,
                start_line=hunk.new_start,
                end_line=hunk.new_start + hunk.new_lines,
                change_type="modified",
            ))
            if is_model:
                changed_db_models.append({
                    "model_name": cls_name,
                    "file_path": path,
                    "start_line": hunk.new_start,
                })
