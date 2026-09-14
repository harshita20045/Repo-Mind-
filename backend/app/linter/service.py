"""
Static analysis orchestration — Phase 9.
"""
import base64
import logging
import os
import tempfile
from typing import List

from sqlalchemy.orm import Session

from backend.app.github.client import GitHubClient, GitHubAPIError
from backend.app.review.models import LinterResult
from backend.app.linter.tools import LinterTool, RuffLinter, BanditLinter

logger = logging.getLogger(__name__)

# Config files we should attempt to fetch from the repository root
CONFIG_FILES = [
    "pyproject.toml",
    "ruff.toml",
    ".ruff.toml",
    "bandit.yaml",
    ".bandit"
]

def _safe_join(base_dir: str, rel_path: str) -> str:
    """Safely join paths to prevent directory traversal."""
    # Normalize path and check prefix
    final_path = os.path.abspath(os.path.join(base_dir, rel_path))
    if not final_path.startswith(os.path.abspath(base_dir)):
        raise ValueError(f"Path traversal detected: {rel_path}")
    return final_path

def run_linters(
    db: Session,
    client: GitHubClient,
    owner: str,
    repo: str,
    pr_number: int,
    review_run_id: int,
) -> None:
    """
    Run static analysis tools against the PR changes.
    1. Fetches modified/added Python files.
    2. Sets up a temporary workspace, preserving paths.
    3. Fetches repository configuration (pyproject.toml, etc).
    4. Runs linters safely.
    5. Persists the results in LinterResult.
    """
    logger.info("Starting Phase 9 linter execution for PR %d (ReviewRun %d)", pr_number, review_run_id)
    
    # 1. Fetch files from PR
    try:
        pr_files = client.get_pull_request_files(owner, repo, pr_number)
    except GitHubAPIError as exc:
        logger.warning("Failed to fetch PR files for linting: %s", str(exc))
        # If we can't fetch files, we create a linter result indicating the failure
        _persist_failure(db, review_run_id, "all", "infrastructure_error", "Failed to fetch PR files")
        return

    # Filter for relevant files (Python only, not deleted)
    files_to_lint = []
    for f in pr_files:
        path = f.get("filename", "")
        status = f.get("status", "")
        
        # Only lint python files that are not removed
        if path.endswith(".py") and status != "removed":
            files_to_lint.append(f)

    if not files_to_lint:
        logger.info("No relevant files to lint for PR %d", pr_number)
        return

    # 2. Setup Temporary Workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        paths_to_lint = []
        
        # Download the files to lint
        for f in files_to_lint:
            path = f.get("filename", "")
            sha = f.get("sha")
            if not sha:
                continue
                
            try:
                secure_path = _safe_join(temp_dir, path)
                # Create parent directories
                os.makedirs(os.path.dirname(secure_path), exist_ok=True)
                
                # Fetch raw blob
                content = client.get_blob_content(owner, repo, sha)
                with open(secure_path, "wb") as out:
                    out.write(content)
                    
                paths_to_lint.append(path)
            except ValueError:
                logger.warning("Skipped unsafe path: %s", path)
            except GitHubAPIError:
                logger.warning("Failed to download blob for %s", path)

        if not paths_to_lint:
            logger.info("No files successfully downloaded for linting.")
            return

        # 3. Fetch repo configuration files to respect repo-specific config safely
        for config_file in CONFIG_FILES:
            try:
                secure_config_path = _safe_join(temp_dir, config_file)
                contents = client.get_repository_contents(owner, repo, config_file)
                if isinstance(contents, dict) and contents.get("type") == "file" and contents.get("encoding") == "base64":
                    file_content = base64.b64decode(contents["content"])
                    with open(secure_config_path, "wb") as out:
                        out.write(file_content)
            except ValueError:
                pass  # Unsafe path
            except GitHubAPIError:
                pass  # File doesn't exist or other API error, ignore safely

        # 4. Run linters
        tools: List[LinterTool] = [RuffLinter(), BanditLinter()]
        for tool in tools:
            try:
                result = tool.execute(temp_dir, paths_to_lint)
                _persist_result(db, review_run_id, tool.name, result)
            except Exception as exc:
                logger.error("Unexpected error running %s: %s", tool.name, str(exc))
                _persist_failure(db, review_run_id, tool.name, "unexpected_error", str(exc))


def _persist_result(db: Session, review_run_id: int, tool_name: str, raw_output: dict) -> None:
    """Persist a structured LinterResult row."""
    lr = LinterResult(
        review_run_id=review_run_id,
        tool=tool_name,
        raw_output=raw_output
    )
    db.add(lr)
    db.commit()


def _persist_failure(db: Session, review_run_id: int, tool_name: str, error_type: str, message: str) -> None:
    """Persist an infrastructure or unexpected failure in LinterResult."""
    _persist_result(db, review_run_id, tool_name, {
        "status": "error",
        "error_type": error_type,
        "message": message
    })
