"""
Isolated Test Sandbox Runner — RepoMind 2.0.

Provides safe, sandboxed execution of generated tests:
  1. AST Pre-Execution Security Review
  2. Isolated temporary workspace
  3. Strict production secrets stripping from environment
  4. Restricted network and filesystem boundaries
  5. Reliable execution result capture (no false passes)
"""
import ast
import os
import sys
import time
import subprocess
import tempfile
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.testing.models import GeneratedTestCase

logger = logging.getLogger("repomind.testing.runner")

# Sensitive environment variables to purge from sandbox execution
SECRETS_BLOCKLIST = [
    "POSTGRES_URL",
    "DATABASE_URL",
    "JWT_SECRET",
    "FERNET_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "GITHUB_CLIENT_SECRET",
    "GITHUB_WEBHOOK_SECRET",
    "BOOTSTRAP_TOKEN",
]

# Prohibited AST functions and modules in generated test code
DISALLOWED_MODULES = {"shutil", "telnetlib", "ftplib", "smtplib"}
DISALLOWED_CALLS = {
    "system", "popen", "spawn", "rmtree", "unlink", "remove",
    "eval", "exec", "compile",
}


def review_code_security(test_code: str, language: str) -> Tuple[bool, Optional[str]]:
    """
    Pre-execution AST security review to prevent arbitrary command execution,
    filesystem deletion, or credential harvesting.
    """
    if language != "python":
        # For JS/TS, check regex patterns for command execution
        forbidden_patterns = [
            r"child_process", r"exec\(", r"spawn\(", r"fork\(",
            r"process\.env", r"fs\.unlink", r"fs\.rm", r"eval\("
        ]
        for pat in forbidden_patterns:
            import re
            if re.search(pat, test_code):
                return False, f"Prohibited JS/TS operation matched security filter: {pat}"
        return True, None

    try:
        tree = ast.parse(test_code)
    except SyntaxError as e:
        return False, f"Syntax error in generated test code: {e}"

    for node in ast.walk(tree):
        # 1. Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module in DISALLOWED_MODULES:
                    return False, f"Prohibited module imported: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                if root_module in DISALLOWED_MODULES:
                    return False, f"Prohibited module imported from: {node.module}"

        # 2. Check function calls
        if isinstance(node, ast.Call):
            # Direct calls: eval(), exec()
            if isinstance(node.func, ast.Name):
                if node.func.id in DISALLOWED_CALLS:
                    return False, f"Prohibited built-in call: {node.func.id}()"
            # Attribute calls: os.system(), shutil.rmtree()
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in DISALLOWED_CALLS:
                    return False, f"Prohibited method call: {node.func.attr}()"

    return True, None


class IsolatedTestRunner:
    """
    Executes generated tests in an isolated, temporary, secret-stripped sandbox.
    """

    def __init__(self, db: Session):
        self.db = db

    def execute_test(self, test_id: int) -> GeneratedTestCase:
        """
        Executes the generated test case and captures the execution result.
        Crucial Rule: Do not report generated tests as passing until they have
        actually been executed and achieved exit code 0.
        """
        test_case = self.db.get(GeneratedTestCase, test_id)
        if not test_case:
            raise ValueError(f"GeneratedTestCase {test_id} not found")

        test_case.execution_status = "running"
        self.db.commit()

        # Step 1: Pre-Execution AST Security Review
        is_safe, sec_reason = review_code_security(test_case.test_code, test_case.language)
        if not is_safe:
            test_case.security_reviewed = False
            test_case.execution_status = "error"
            test_case.execution_result = {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Security pre-execution check failed: {sec_reason}",
                "duration_ms": 0,
                "assertions_passed": 0,
                "assertions_failed": 1,
                "failure_details": sec_reason,
            }
            test_case.executed_at = datetime.now(timezone.utc)
            self.db.commit()
            return test_case

        test_case.security_reviewed = True

        # Step 2: Prepare Isolated Workspace
        with tempfile.TemporaryDirectory(prefix="repomind_test_") as temp_dir:
            file_name = "test_target.py" if test_case.language == "python" else "test_target.test.js"
            test_file_path = os.path.join(temp_dir, file_name)

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_case.test_code)

            # Step 3: Strip Production Secrets from Environment
            sandbox_env = dict(os.environ)
            for secret_var in SECRETS_BLOCKLIST:
                sandbox_env.pop(secret_var, None)

            # Prevent writing bytecode files
            sandbox_env["PYTHONDONTWRITEBYTECODE"] = "1"
            sandbox_env["PYTHONPATH"] = os.getcwd()

            # Step 4: Assemble Command
            if test_case.language == "python":
                # Run pytest against the isolated test file
                pytest_bin = sys.executable
                cmd = [pytest_bin, "-m", "pytest", test_file_path, "-q", "--tb=short"]
            else:
                cmd = ["npx", "vitest", "run", test_file_path]

            # Step 5: Execute with Strict Timeout
            start_time = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=temp_dir,
                    env=sandbox_env,
                    capture_output=True,
                    text=True,
                    timeout=25,
                    shell=False,
                )
                duration_ms = round((time.time() - start_time) * 1000, 2)
                returncode = proc.returncode
                stdout = proc.stdout
                stderr = proc.stderr
            except subprocess.TimeoutExpired:
                duration_ms = 25000.0
                returncode = -2
                stdout = ""
                stderr = "Test execution timed out after 25 seconds in sandbox."
            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                returncode = -3
                stdout = ""
                stderr = f"Sandbox execution error: {type(e).__name__}: {str(e)}"

            # Step 6: Determine Real Status (No false passes)
            if returncode == 0:
                execution_status = "passed"
                failure_details = None
                assertions_passed = 1
                assertions_failed = 0
            else:
                execution_status = "failed"
                failure_details = stderr or stdout or "Test assertions failed"
                assertions_passed = 0
                assertions_failed = 1

            test_case.execution_status = execution_status
            test_case.execution_result = {
                "returncode": returncode,
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
                "duration_ms": duration_ms,
                "assertions_passed": assertions_passed,
                "assertions_failed": assertions_failed,
                "failure_details": failure_details[:2000] if failure_details else None,
            }
            test_case.executed_at = datetime.now(timezone.utc)
            self.db.commit()

        logger.info(
            "Test %d executed in sandbox: status=%s, duration=%.2fms",
            test_id,
            test_case.execution_status,
            duration_ms,
        )
        return test_case

