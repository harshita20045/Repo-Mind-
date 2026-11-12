import json
import logging
import subprocess
from typing import Protocol, Any, Dict, List

logger = logging.getLogger(__name__)

class LinterTool(Protocol):
    """
    Protocol for static analysis tools.
    """
    @property
    def name(self) -> str:
        ...

    def execute(self, workspace_path: str, files_to_lint: List[str]) -> Dict[str, Any]:
        """
        Execute the linter in the given workspace.
        
        Args:
            workspace_path: Absolute path to the temporary directory containing repo files.
            files_to_lint: List of relative file paths to lint.
            
        Returns:
            A dictionary to be stored in LinterResult.raw_output.
            Must contain at least "status" ("success", "failure", "error")
            and "output" or "findings".
        """
        ...


class RuffLinter:
    """
    Executes Ruff against the workspace.
    """
    @property
    def name(self) -> str:
        return "ruff"

    def execute(self, workspace_path: str, files_to_lint: List[str]) -> Dict[str, Any]:
        if not files_to_lint:
            return {
                "status": "success",
                "results": [],
                "findings": [],
                "raw_findings": []
            }
            
        try:
            # We run ruff check --output-format json on the specific files
            # No shell=True. Explicit arguments.
            cmd = ["ruff", "check", "--output-format", "json"] + files_to_lint
            
            result = subprocess.run(
                cmd,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            # Ruff exits with 0 if no violations, 1 if violations found.
            # Both are considered successful execution.
            if result.returncode not in (0, 1):
                return {
                    "status": "error",
                    "error_type": "execution_failed",
                    "returncode": result.returncode,
                    "stderr": result.stderr[:1000],
                    "results": [],
                    "findings": [],
                    "raw_findings": None,
                }
                
            try:
                # If output is empty but return code is 0, it means no findings.
                if not result.stdout.strip():
                    raw_findings = []
                else:
                    raw_findings = json.loads(result.stdout)

                if not isinstance(raw_findings, list):
                    return {
                        "status": "error",
                        "error_type": "invalid_schema",
                        "results": [],
                        "findings": [],
                        "raw_findings": raw_findings,
                    }

                normalized = []
                for item in raw_findings:
                    if isinstance(item, dict):
                        loc = item.get("location") if isinstance(item.get("location"), dict) else {}
                        normalized.append({
                            "tool": "ruff",
                            "file": item.get("filename"),
                            "filename": item.get("filename"),
                            "line": loc.get("row"),
                            "column": loc.get("column"),
                            "code": item.get("code"),
                            "message": item.get("message"),
                            "severity": "medium",
                        })

                return {
                    "status": "success",
                    "results": normalized,
                    "findings": raw_findings,
                    "raw_findings": raw_findings,
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "error_type": "invalid_json",
                    "stdout": result.stdout[:1000],
                    "results": [],
                    "findings": [],
                    "raw_findings": None,
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error_type": "timeout", "results": [], "findings": [], "raw_findings": None}
        except FileNotFoundError:
            return {"status": "error", "error_type": "executable_missing", "results": [], "findings": [], "raw_findings": None}
        except Exception as exc:
            return {"status": "error", "error_type": "unexpected_error", "message": type(exc).__name__, "results": [], "findings": [], "raw_findings": None}


class BanditLinter:
    """
    Executes Bandit against the workspace.
    """
    @property
    def name(self) -> str:
        return "bandit"

    def execute(self, workspace_path: str, files_to_lint: List[str]) -> Dict[str, Any]:
        if not files_to_lint:
            return {
                "status": "success",
                "results": [],
                "findings": {"results": []},
                "raw_findings": {"results": []}
            }
            
        try:
            # bandit -f json
            cmd = ["bandit", "-f", "json"] + files_to_lint
            
            result = subprocess.run(
                cmd,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            # Bandit exits 0 if no issues, 1 if issues found
            # (or other codes if there's a problem, e.g. 2 for usage error)
            if result.returncode not in (0, 1):
                return {
                    "status": "error",
                    "error_type": "execution_failed",
                    "returncode": result.returncode,
                    "stderr": result.stderr[:1000],
                    "results": [],
                    "findings": {"results": []},
                    "raw_findings": None,
                }
                
            try:
                if not result.stdout.strip():
                    raw_findings = {"results": []}
                else:
                    raw_findings = json.loads(result.stdout)

                if not isinstance(raw_findings, dict):
                    return {
                        "status": "error",
                        "error_type": "invalid_schema",
                        "results": [],
                        "findings": {"results": []},
                        "raw_findings": raw_findings,
                    }

                bandit_issues = raw_findings.get("results", [])
                normalized = []
                if isinstance(bandit_issues, list):
                    for item in bandit_issues:
                        if isinstance(item, dict):
                            sev = str(item.get("issue_severity", "medium")).lower()
                            normalized.append({
                                "tool": "bandit",
                                "file": item.get("filename"),
                                "filename": item.get("filename"),
                                "line": item.get("line_number"),
                                "code": item.get("test_id"),
                                "message": item.get("issue_text"),
                                "severity": sev,
                            })

                return {
                    "status": "success",
                    "results": normalized,
                    "findings": raw_findings,
                    "raw_findings": raw_findings,
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "error_type": "invalid_json",
                    "stdout": result.stdout[:1000],
                    "results": [],
                    "findings": {"results": []},
                    "raw_findings": None,
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error_type": "timeout", "results": [], "findings": {"results": []}, "raw_findings": None}
        except FileNotFoundError:
            return {"status": "error", "error_type": "executable_missing", "results": [], "findings": {"results": []}, "raw_findings": None}
        except Exception as exc:
            return {"status": "error", "error_type": "unexpected_error", "message": type(exc).__name__, "results": [], "findings": {"results": []}, "raw_findings": None}
