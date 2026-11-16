"""
Architecture Rule Checker & Compliance Auditor — RepoMind 2.0.

Evaluates repository code imports, cross-layer boundaries, and flows
against active repository architecture rules to generate grounded violation findings.
"""
import fnmatch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
import re

from backend.app.architecture.layers import classify_layer, get_layer_rank
from backend.app.architecture.circular import CircularDependency
from backend.app.architecture.flows import FlowAnalysisResult


@dataclass
class GroundedViolation:
    rule_code: str
    rule_id: Optional[int]
    violation_type: str  # forbidden_dependency | circular_dependency | leaky_flow | layer_violation
    severity: str        # critical | high | medium | low
    title: str
    explanation: str
    suggested_correction: str
    source_file: str
    source_line: Optional[int] = None
    target_file: Optional[str] = None
    target_line: Optional[int] = None
    evidence: Optional[str] = None


def _matches_pattern(file_path: str, pattern: Optional[str]) -> bool:
    """Tests if a normalized file path matches a pipe-separated glob pattern list."""
    if not pattern or not pattern.strip():
        return False

    clean = file_path.replace("\\", "/").strip("/")
    subpatterns = [p.strip() for p in pattern.split("|") if p.strip()]

    for sub in subpatterns:
        if fnmatch.fnmatch(clean, sub):
            return True
        if fnmatch.fnmatch(clean, f"*/{sub}") or fnmatch.fnmatch(clean, f"{sub}/*"):
            return True
        # Substring containment fallback for simple names
        if "/" not in sub and "*" not in sub and sub in clean.lower():
            return True

    return False


def check_architecture_rules(
    active_rules: List[Dict[str, Any]],
    import_records: List[Dict[str, Any]],  # [{source_file, target_file, imported_names, line, raw_statement}]
    circular_dependencies: List[CircularDependency],
    flow_results: FlowAnalysisResult,
) -> List[GroundedViolation]:
    """
    Audits imports and execution flows against enabled architecture rules.
    """
    violations: List[GroundedViolation] = []
    seen_violation_keys: Set[str] = set()

    # Index active rules by type and code
    rule_by_code = {r.get("rule_code"): r for r in active_rules}

    # 1. Audit Imports against Forbidden Dependency & Layer Rules
    for imp in import_records:
        src = imp.get("source_file", "")
        tgt = imp.get("target_file", "")
        line = imp.get("line")
        raw_stmt = imp.get("raw_statement") or f"import {tgt}"

        if not src or not tgt or src == tgt:
            continue

        src_layer = classify_layer(src)
        tgt_layer = classify_layer(tgt)

        for rule in active_rules:
            if not rule.get("is_enabled", True):
                continue

            rtype = rule.get("rule_type")
            rcode = rule.get("rule_code", "ARCH-RULE")
            rule_id = rule.get("id")
            severity = rule.get("severity", "high")
            suggested_fix = rule.get("suggested_fix") or "Refactor code to respect architectural boundaries."

            # A. Layer Boundary & Forbidden Dependency
            if rtype in ("forbidden_dependency", "layer_boundary"):
                rule_src_layer = rule.get("source_layer")
                rule_tgt_layer = rule.get("target_layer")
                rule_src_pat = rule.get("source_pattern")
                rule_tgt_pat = rule.get("target_pattern")

                matches_src = False
                if rule_src_layer and rule_src_layer == src_layer:
                    matches_src = True
                elif rule_src_pat and _matches_pattern(src, rule_src_pat):
                    matches_src = True

                matches_tgt = False
                if rule_tgt_layer:
                    if rule_tgt_layer == "backend":
                        matches_tgt = (
                            tgt_layer in ("presentation", "business_logic", "data_access", "infrastructure", "domain", "worker")
                            or "backend/" in tgt.lower()
                            or "server/" in tgt.lower()
                        )
                    elif rule_tgt_layer == tgt_layer:
                        matches_tgt = True
                elif rule_tgt_pat and _matches_pattern(tgt, rule_tgt_pat):
                    matches_tgt = True

                if matches_src and matches_tgt:
                    vkey = f"{rcode}:{src}:{tgt}:{line}"
                    if vkey not in seen_violation_keys:
                        seen_violation_keys.add(vkey)
                        violations.append(GroundedViolation(
                            rule_code=rcode,
                            rule_id=rule_id,
                            violation_type=rtype,
                            severity=severity,
                            title=rule.get("name", f"Forbidden Dependency Violation ({rcode})"),
                            explanation=rule.get("description") or f"Module '{src}' (layer: {src_layer}) is prohibited from importing '{tgt}' (layer: {tgt_layer}).",
                            suggested_correction=suggested_fix,
                            source_file=src,
                            source_line=line,
                            target_file=tgt,
                            target_line=None,
                            evidence=raw_stmt,
                        ))

            # B. API-to-DB Direct Access Check (ARCH-001)
            elif rtype == "api_db_isolation":
                rule_src_pat = rule.get("source_pattern")
                rule_tgt_pat = rule.get("target_pattern")
                is_presentation = (src_layer == "presentation") or (bool(rule_src_pat) and _matches_pattern(src, rule_src_pat))
                is_data = (tgt_layer == "data_access") or (bool(rule_tgt_pat) and _matches_pattern(tgt, rule_tgt_pat))

                if is_presentation and is_data:
                    vkey = f"{rcode}:{src}:{tgt}:{line}"
                    if vkey not in seen_violation_keys:
                        seen_violation_keys.add(vkey)
                        violations.append(GroundedViolation(
                            rule_code=rcode,
                            rule_id=rule_id,
                            violation_type="forbidden_dependency",
                            severity=severity,
                            title=rule.get("name", "Controller Directly Accessing Database Model"),
                            explanation=f"Route/Controller '{src}' directly imports database model '{tgt}'. This violates layer isolation and prevents centralized business rule enforcement.",
                            suggested_correction=suggested_fix,
                            source_file=src,
                            source_line=line,
                            target_file=tgt,
                            target_line=None,
                            evidence=raw_stmt,
                        ))

    # 2. Audit Leaky Execution Flows (Direct DB operations from routes)
    api_db_rule = rule_by_code.get("ARCH-001")
    if api_db_rule and api_db_rule.get("is_enabled", True):
        for leaky in flow_results.leaky_flows:
            vkey = f"LEAKY:{leaky.route_file}:{leaky.endpoint_name}"
            if vkey not in seen_violation_keys:
                seen_violation_keys.add(vkey)
                violations.append(GroundedViolation(
                    rule_code="ARCH-001",
                    rule_id=api_db_rule.get("id"),
                    violation_type="leaky_flow",
                    severity="critical",
                    title=f"Leaky Route Execution Flow: {leaky.endpoint_name}",
                    explanation=f"Endpoint '{leaky.endpoint_name}' in {leaky.route_file} performs database operations without delegating to a service layer.",
                    suggested_correction=leaky.suggested_fix or "Wrap the model query inside a dedicated service function and call it from the route handler.",
                    source_file=leaky.route_file,
                    evidence=leaky.evidence,
                ))

    # 3. Audit Circular Dependencies (ARCH-005)
    cycle_rule = rule_by_code.get("ARCH-005")
    if cycle_rule and cycle_rule.get("is_enabled", True):
        for cycle in circular_dependencies:
            src_f = cycle.participating_files[0] if cycle.participating_files else ""
            tgt_f = cycle.participating_files[1] if len(cycle.participating_files) > 1 else ""
            vkey = f"CYCLE:{src_f}:{tgt_f}:{cycle.length}"
            if vkey not in seen_violation_keys:
                seen_violation_keys.add(vkey)
                violations.append(GroundedViolation(
                    rule_code="ARCH-005",
                    rule_id=cycle_rule.get("id"),
                    violation_type="circular_dependency",
                    severity=cycle.severity,
                    title=cycle.title,
                    explanation=cycle.explanation,
                    suggested_correction=cycle.decoupling_recommendation,
                    source_file=src_f,
                    target_file=tgt_f,
                    evidence=f"Cycle loop: {' -> '.join(cycle.cycle_path)}",
                ))

    return violations
