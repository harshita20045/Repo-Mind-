import json
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from backend.app.linter.tools import RuffLinter, BanditLinter
from backend.app.linter.service import run_linters, CONFIG_FILES
from backend.app.github.client import GitHubClient, GitHubAPIError
from backend.app.review.models import ReviewRun, LinterResult


def test_ruff_linter_success():
    """Test Ruff linter parsing success."""
    tool = RuffLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, # Violations found
            stdout=json.dumps([{"message": "Line too long"}]),
            stderr=""
        )
        
        result = tool.execute("/tmp/workspace", ["test.py"])
        assert result["status"] == "success"
        assert len(result["findings"]) == 1
        assert result["findings"][0]["message"] == "Line too long"
        
        # Verify subprocess was called correctly (shell=False)
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False
        assert kwargs["cwd"] == "/tmp/workspace"
        assert kwargs["timeout"] == 30
        assert args[0] == ["ruff", "check", "--output-format", "json", "test.py"]


def test_bandit_linter_success():
    """Test Bandit linter parsing success."""
    tool = BanditLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, # Issues found
            stdout=json.dumps({"results": [{"issue_text": "Use of exec"}]}),
            stderr=""
        )
        
        result = tool.execute("/tmp/workspace", ["test.py"])
        assert result["status"] == "success"
        assert "results" in result["findings"]
        assert result["findings"]["results"][0]["issue_text"] == "Use of exec"
        
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False
        assert args[0] == ["bandit", "-f", "json", "test.py"]


def test_linter_timeout():
    """Test linter timeout handling."""
    tool = RuffLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ruff", timeout=30)
        
        result = tool.execute("/tmp/workspace", ["test.py"])
        assert result["status"] == "error"
        assert result["error_type"] == "timeout"


def test_linter_invalid_json():
    """Test linter recovery from unparseable JSON."""
    tool = RuffLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Not a json output",
            stderr=""
        )
        
        result = tool.execute("/tmp/workspace", ["test.py"])
        assert result["status"] == "error"
        assert result["error_type"] == "invalid_json"


from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest

def _setup_pr(db_session):
    org = Organization(name="test")
    db_session.add(org)
    db_session.commit()
    proj = Project(organization_id=org.id, name="test")
    db_session.add(proj)
    db_session.commit()
    repo = Repository(project_id=proj.id, github_owner="test", github_name="test")
    db_session.add(repo)
    db_session.commit()
    from datetime import datetime, timezone
    pr = PullRequest(repository_id=repo.id, github_number=1, title="test", state="open", head_sha="abcd", created_at=datetime.now(timezone.utc))
    db_session.add(pr)
    db_session.commit()
    return pr.id

def test_run_linters_orchestration(db_session):
    """Test the full run_linters service orchestration."""
    pr_id = _setup_pr(db_session)
    # 1. Setup a ReviewRun in the DB
    run = ReviewRun(
        pull_request_id=pr_id,
        commit_sha="abcd",
        status="running",
        repomind_version="test",
        prompt_version="test",
        llm_model="test",
        rag_enabled=True,
    )
    db_session.add(run)
    db_session.commit()
    
    # 2. Mock GitHubClient
    mock_client = MagicMock(spec=GitHubClient)
    
    # Return two files: one valid python, one deleted, one non-python
    mock_client.get_pull_request_files.return_value = [
        {"filename": "main.py", "status": "modified", "sha": "1111"},
        {"filename": "deleted.py", "status": "removed", "sha": "2222"},
        {"filename": "readme.md", "status": "added", "sha": "3333"},
        {"filename": "../traversal.py", "status": "added", "sha": "4444"},
    ]
    
    # Mock blob download
    mock_client.get_blob_content.return_value = b"print('hello')"
    
    # Mock config fetch: return base64 encoded pyproject.toml for the first one, API error for rest
    def mock_get_repo_contents(*args, **kwargs):
        path = args[2]
        if path == "pyproject.toml":
            return {"type": "file", "encoding": "base64", "content": "W3Rvb2wucnVmZl0="} # [tool.ruff]
        raise GitHubAPIError(404, "Not found")
    
    mock_client.get_repository_contents.side_effect = mock_get_repo_contents
    
    # 3. Run orchestration, patching the LinterTool executions to avoid running real binaries
    with patch("backend.app.linter.tools.RuffLinter.execute") as mock_ruff, \
         patch("backend.app.linter.tools.BanditLinter.execute") as mock_bandit:
         
        mock_ruff.return_value = {"status": "success", "findings": []}
        mock_bandit.return_value = {"status": "success", "findings": {}}
        
        run_linters(
            db=db_session,
            client=mock_client,
            owner="test_owner",
            repo="test_repo",
            pr_number=1,
            review_run_id=run.id,
        )
        
        # Verify tools were called exactly with "main.py" (skips deleted, non-py, and traversal)
        mock_ruff.assert_called_once()
        args, _ = mock_ruff.call_args
        assert args[1] == ["main.py"]
        
        mock_bandit.assert_called_once()
        args, _ = mock_bandit.call_args
        assert args[1] == ["main.py"]

    # 4. Verify DB persistence
    results = db_session.query(LinterResult).filter(LinterResult.review_run_id == run.id).all()
    assert len(results) == 2
    
    tools_run = {r.tool for r in results}
    assert tools_run == {"ruff", "bandit"}
    
    for r in results:
        assert r.raw_output["status"] == "success"


def test_run_linters_fetch_error(db_session):
    """Test that failure to fetch files doesn't crash the review but stores a failure result."""
    pr_id = _setup_pr(db_session)
    run = ReviewRun(pull_request_id=pr_id, commit_sha="abcd", status="running", repomind_version="t", prompt_version="t", llm_model="t", rag_enabled=True)
    db_session.add(run)
    db_session.commit()
    
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.get_pull_request_files.side_effect = GitHubAPIError(403, "API rate limit")
    
    run_linters(
        db=db_session,
        client=mock_client,
        owner="test_owner",
        repo="test_repo",
        pr_number=1,
        review_run_id=run.id,
    )
    
    results = db_session.query(LinterResult).filter(LinterResult.review_run_id == run.id).all()
    assert len(results) == 1
    assert results[0].tool == "all"
    assert results[0].raw_output["status"] == "error"
    assert results[0].raw_output["error_type"] == "infrastructure_error"
