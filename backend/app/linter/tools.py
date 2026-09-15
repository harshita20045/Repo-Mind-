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
            return {"status": "success", "findings": []}
            
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
                    "stderr": result.stderr[:1000]
                }
                
            try:
                # If output is empty but return code is 0, it means no findings.
                if not result.stdout.strip():
                    findings = []
                else:
                    findings = json.loads(result.stdout)
                return {"status": "success", "findings": findings}
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "error_type": "invalid_json",
                    "stdout": result.stdout[:1000]
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error_type": "timeout"}
        except FileNotFoundError:
            return {"status": "error", "error_type": "executable_missing"}
        except Exception as exc:
            return {"status": "error", "error_type": "unexpected_error", "message": type(exc).__name__}


class BanditLinter:
    """
    Executes Bandit against the workspace.
    """
    @property
    def name(self) -> str:
        return "bandit"

    def execute(self, workspace_path: str, files_to_lint: List[str]) -> Dict[str, Any]:
        if not files_to_lint:
            return {"status": "success", "findings": []}
            
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
                    "stderr": result.stderr[:1000]
                }
                
            try:
                if not result.stdout.strip():
                    findings = {}
                else:
                    findings = json.loads(result.stdout)
                return {"status": "success", "findings": findings}
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "error_type": "invalid_json",
                    "stdout": result.stdout[:1000]
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error_type": "timeout"}
        except FileNotFoundError:
            return {"status": "error", "error_type": "executable_missing"}
        except Exception as exc:
            return {"status": "error", "error_type": "unexpected_error", "message": type(exc).__name__}
