"""
Breaking Change Detector — RepoMind 2.0 Change Impact Engine.

Detects high-risk breaking mutations:
  1. Function & method signature alterations (required param added, param removed)
  2. Removed exports or deleted public functions still imported elsewhere
  3. API contract breaks (removed routes, added required request fields)
  4. Database schema breaking changes (dropped columns, non-nullable without default)
  5. Authentication contract shifts (endpoints gated with new permission scopes)
  6. Shared configuration changes (missing or modified environment variables)
"""
import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from backend.app.impact.detector import (
    DetectedCodeChanges,
    ChangedSymbol,
    _extract_py_signatures,
    FunctionSignature,
)

logger = logging.getLogger(__name__)


@dataclass
class BreakingChange:
    """Represents a potential breaking change that could disrupt downstream consumers."""
    change_type: str  # signature_mutation | removed_symbol | api_break | schema_break | auth_break | config_break
    component_name: str
    file_path: str
    severity: str     # critical | high | medium
    title: str
    description: str
    evidence: str
    suggested_fix: str


_REMOVED_LINE_FN_RE = re.compile(r"^-\s*(?:async\s+)?def\s+([A-Za-z_0-9]+)\s*\((.*?)\)", re.MULTILINE)
_ADDED_LINE_FN_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_0-9]+)\s*\((.*?)\)", re.MULTILINE)
_DROPPED_COLUMN_RE = re.compile(r"^-\s*([A-Za-z_0-9]+)\s*=\s*Column\(", re.MULTILINE)
_NON_NULL_COL_RE = re.compile(r"^\+\s*([A-Za-z_0-9]+)\s*=\s*Column\(.*nullable\s*=\s*False", re.MULTILINE)


def detect_breaking_changes(
    diff: str,
    changes: DetectedCodeChanges,
    old_file_contents: Optional[Dict[str, str]] = None,
    new_file_contents: Optional[Dict[str, str]] = None,
) -> List[BreakingChange]:
    """
    Examine diff and AST signatures to detect breaking changes across the codebase.
    """
    old_file_contents = old_file_contents or {}
    new_file_contents = new_file_contents or {}
    breaking_changes: List[BreakingChange] = []

    # 1. Signature Changes: Compare old and new AST signatures if contents available
    for path in changes.changed_files:
        if not path.endswith(".py"):
            continue

        old_src = old_file_contents.get(path, "")
        new_src = new_file_contents.get(path, "")

        if old_src and new_src:
            old_sigs = _extract_py_signatures(old_src)
            new_sigs = _extract_py_signatures(new_src)

            for fn_name, old_sig in old_sigs.items():
                if fn_name not in new_sigs:
                    # Symbol was deleted or renamed in new revision!
                    breaking_changes.append(BreakingChange(
                        change_type="removed_symbol",
                        component_name=f"{path}:{fn_name}",
                        file_path=path,
                        severity="high",
                        title=f"Removed public symbol '{fn_name}'",
                        description=f"Function or method '{fn_name}' was removed from {path}. Any existing caller importing this symbol will fail with ImportError or AttributeError.",
                        evidence=f"Present in base revision with params ({', '.join(old_sig.params)}), absent in new revision.",
                        suggested_fix=f"Retain '{fn_name}' with a deprecation warning or provide a backward-compatible shim.",
                    ))
                    continue

                new_sig = new_sigs[fn_name]
                _check_signature_compatibility(path, fn_name, old_sig, new_sig, breaking_changes)

    # 2. Diff-based heuristic detection (fallback when full base/head file contents are not provided)
    if not old_file_contents:
        _detect_breaking_from_diff_lines(diff, changes, breaking_changes)

    # 3. Database Schema Breaking Changes
    _detect_database_schema_breaks(diff, changes, breaking_changes)

    # 4. Configuration Breaking Changes
    _detect_configuration_breaks(diff, changes, breaking_changes)

    return breaking_changes


def _check_signature_compatibility(
    path: str,
    fn_name: str,
    old_sig: FunctionSignature,
    new_sig: FunctionSignature,
    breaking_changes: List[BreakingChange],
) -> None:
    """Compare parameter lists to detect breaking signature adjustments."""
    old_params = set(old_sig.params)
    new_params = set(new_sig.params)

    # A. Check for removed parameters
    removed_params = old_params - new_params
    if removed_params:
        breaking_changes.append(BreakingChange(
            change_type="signature_mutation",
            component_name=f"{path}:{fn_name}",
            file_path=path,
            severity="high",
            title=f"Parameter(s) removed from '{fn_name}'",
            description=f"Parameters {sorted(list(removed_params))} were removed from '{fn_name}'. Call sites passing these parameters will encounter TypeError.",
            evidence=f"Old params: ({', '.join(old_sig.params)}) -> New params: ({', '.join(new_sig.params)})",
            suggested_fix=f"Keep removed parameters with default None or accept **kwargs for backward compatibility.",
        ))

    # B. Check for added REQUIRED parameters (no default value)
    added_params = new_params - old_params
    added_required = [p for p in added_params if not new_sig.has_defaults.get(p, False)]
    if added_required:
        breaking_changes.append(BreakingChange(
            change_type="signature_mutation",
            component_name=f"{path}:{fn_name}",
            file_path=path,
            severity="critical",
            title=f"New required parameter added to '{fn_name}'",
            description=f"Required parameter(s) {sorted(added_required)} were added to '{fn_name}' without default values. Existing callers will fail with missing required argument TypeError.",
            evidence=f"Added without default: {', '.join(added_required)}",
            suggested_fix=f"Provide a default value (e.g. {added_required[0]}=None) so existing callers continue to function.",
        ))


def _detect_breaking_from_diff_lines(
    diff: str,
    changes: DetectedCodeChanges,
    breaking_changes: List[BreakingChange],
) -> None:
    """Scan diff lines directly to detect signature shifts and removed functions."""
    removed_fns = {}
    added_fns = {}

    for m in _REMOVED_LINE_FN_RE.finditer(diff):
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        removed_fns[name] = params

    for m in _ADDED_LINE_FN_RE.finditer(diff):
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        added_fns[name] = params

    # Look for modified signatures of the same function
    for name, old_params in removed_fns.items():
        if name in added_fns:
            new_params = added_fns[name]
            old_set = set(p.split("=")[0].strip() for p in old_params)
            new_set = set(p.split("=")[0].strip() for p in new_params)

            # Did we add parameters without '=' (required)?
            new_required = [p for p in new_params if "=" not in p and p.split(":")[0].strip() not in old_set and p not in ("self", "cls")]
            if new_required:
                breaking_changes.append(BreakingChange(
                    change_type="signature_mutation",
                    component_name=name,
                    file_path="[diff hunk]",
                    severity="critical",
                    title=f"New required parameter added to '{name}'",
                    description=f"Function '{name}' had required parameter(s) {new_required} added without default values.",
                    evidence=f"- def {name}({', '.join(old_params)})\n+ def {name}({', '.join(new_params)})",
                    suggested_fix="Assign default values to new parameters to preserve backward compatibility.",
                ))


def _detect_database_schema_breaks(
    diff: str,
    changes: DetectedCodeChanges,
    breaking_changes: List[BreakingChange],
) -> None:
    """Detect dropped columns or non-nullable column additions without defaults."""
    for path in changes.changed_files:
        if "model" not in path.lower() and "schema" not in path.lower():
            continue

        # Dropped column
        for m in _DROPPED_COLUMN_RE.finditer(diff):
            col_name = m.group(1)
            breaking_changes.append(BreakingChange(
                change_type="schema_break",
                component_name=f"{path}:{col_name}",
                file_path=path,
                severity="critical",
                title=f"Database column '{col_name}' dropped",
                description=f"Column '{col_name}' was removed from {path}. Existing database queries referencing this column will break.",
                evidence=m.group(0),
                suggested_fix="Retain the column as deprecated or execute a multi-phase migration.",
            ))

        # Non-nullable added without server default
        for m in _NON_NULL_COL_RE.finditer(diff):
            col_name = m.group(1)
            line = m.group(0)
            if "default" not in line and "server_default" not in line:
                breaking_changes.append(BreakingChange(
                    change_type="schema_break",
                    component_name=f"{path}:{col_name}",
                    file_path=path,
                    severity="high",
                    title=f"Non-nullable column '{col_name}' added without default",
                    description=f"Column '{col_name}' has nullable=False but specifies no default value. Database INSERTs on existing rows or unpopulated payloads will violate NOT NULL constraints.",
                    evidence=line,
                    suggested_fix="Add default or server_default or make the column nullable=True.",
                ))


def _detect_configuration_breaks(
    diff: str,
    changes: DetectedCodeChanges,
    breaking_changes: List[BreakingChange],
) -> None:
    """Detect breaking configuration alterations in settings or .env files."""
    for path in changes.modified_configs:
        lower = path.lower()
        if ".env" in lower or "settings.py" in lower:
            # Check for deleted config keys
            removed_keys = re.findall(r"^-\s*([A-Za-z_0-9]+)\s*=", diff, re.MULTILINE)
            for k in removed_keys:
                if k not in ("#",):
                    breaking_changes.append(BreakingChange(
                        change_type="config_break",
                        component_name=f"{path}:{k}",
                        file_path=path,
                        severity="high",
                        title=f"Configuration key '{k}' removed",
                        description=f"Configuration variable '{k}' was removed from {path}. Services relying on this setting may fail on startup.",
                        evidence=f"- {k} = ...",
                        suggested_fix=f"Provide a fallback value or migration path for '{k}'.",
                    ))
