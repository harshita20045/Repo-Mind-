"""
Regression tests for DEF-01: Linter Output Contract and Multi-schema Consistency.
Verifies canonical schema {"status", "results", "raw_findings"} across Ruff and Bandit,
safe extraction in review/evidence.py, and risk scoring in risk/engine.py.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from backend.app.linter.tools import RuffLinter, BanditLinter
from backend.app.review.evidence import _extract_linter_issues, validate_findings, FindingSchema
from backend.app.risk.engine import calculate_risk


def test_ruff_canonical_schema_with_findings():
    """Verify Ruff produces canonical schema and evidence/risk consume it."""
    ruff = RuffLinter()
    mock_findings = [
        {
            "code": "F401",
            "message": "`os` imported but unused",
            "filename": "backend/app/main.py",
            "location": {"row": 5, "column": 1},
            "end_location": {"row": 5, "column": 10},
        }
    ]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=json.dumps(mock_findings),
            stderr="",
        )
        out = ruff.execute("/tmp/test", ["backend/app/main.py"])

    assert out["status"] == "success"
    assert "results" in out
    assert len(out["results"]) == 1
    assert out["results"][0]["file"] == "backend/app/main.py"
    assert out["results"][0]["line"] == 5
    assert out["results"][0]["code"] == "F401"
    assert out["results"][0]["message"] == "`os` imported but unused"
    assert "raw_findings" in out

    # Test evidence extraction
    linter_results = [{"tool": "ruff", "raw_output": out}]
    issues = _extract_linter_issues(linter_results)
    assert len(issues) == 1
    assert issues[0]["tool"] == "ruff"
    assert issues[0]["file"] == "backend/app/main.py"
    assert issues[0]["line"] == 5

    # Test risk engine complexity scoring
    risk = calculate_risk(
        diff="--- a/backend/app/main.py\n+++ b/backend/app/main.py\n@@ -5,1 +5,1 @@\n+import os",
        validated_findings=[],
        conflicts=[],
        linter_results=linter_results,
        changed_files=["backend/app/main.py"],
        additions=1,
        deletions=0,
    )
    assert any("1 linter issue(s)" in r for r in risk.factors["code_complexity"]["reasons"])


def test_bandit_canonical_schema_with_findings():
    """Verify Bandit produces canonical schema and evidence/risk consume it."""
    bandit = BanditLinter()
    mock_bandit_raw = {
        "results": [
            {
                "filename": "backend/app/auth.py",
                "line_number": 42,
                "test_id": "B101",
                "issue_text": "Use of assert detected.",
                "issue_severity": "LOW",
            }
        ],
        "metrics": {},
        "errors": [],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=json.dumps(mock_bandit_raw),
            stderr="",
        )
        out = bandit.execute("/tmp/test", ["backend/app/auth.py"])

    assert out["status"] == "success"
    assert "results" in out
    assert len(out["results"]) == 1
    assert out["results"][0]["file"] == "backend/app/auth.py"
    assert out["results"][0]["line"] == 42
    assert out["results"][0]["code"] == "B101"
    assert out["results"][0]["severity"] == "low"
    assert out["results"][0]["message"] == "Use of assert detected."

    # Test evidence extraction
    linter_results = [{"tool": "bandit", "raw_output": out}]
    issues = _extract_linter_issues(linter_results)
    assert len(issues) == 1
    assert issues[0]["tool"] == "bandit"
    assert issues[0]["file"] == "backend/app/auth.py"
    assert issues[0]["line"] == 42

    # Test risk engine complexity scoring
    risk = calculate_risk(
        diff="--- a/backend/app/auth.py\n+++ b/backend/app/auth.py\n@@ -42,1 +42,1 @@\n+assert True",
        validated_findings=[],
        conflicts=[],
        linter_results=linter_results,
        changed_files=["backend/app/auth.py"],
        additions=1,
        deletions=0,
    )
    assert any("1 linter issue(s)" in r for r in risk.factors["code_complexity"]["reasons"])


def test_empty_linter_findings():
    """Verify clean runs produce empty results list without errors."""
    ruff = RuffLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        out = ruff.execute("/tmp/test", ["clean.py"])

    assert out["status"] == "success"
    assert out["results"] == []

    issues = _extract_linter_issues([{"tool": "ruff", "raw_output": out}])
    assert len(issues) == 0

    risk = calculate_risk(
        diff="",
        validated_findings=[],
        conflicts=[],
        linter_results=[{"tool": "ruff", "raw_output": out}],
        changed_files=["clean.py"],
        additions=0,
        deletions=0,
    )
    assert not any("linter issue(s)" in r for r in risk.factors["code_complexity"]["reasons"])


def test_malformed_and_unexpected_linter_output():
    """Verify invalid JSON or malformed schema does not crash evidence or risk calculation."""
    ruff = RuffLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="{malformed: json", stderr="")
        out = ruff.execute("/tmp/test", ["foo.py"])

    assert out["status"] == "error"
    assert out["error_type"] == "invalid_json"
    assert out["results"] == []

    # Evidence extraction handles safely
    issues = _extract_linter_issues([{"tool": "ruff", "raw_output": out}])
    assert issues == []

    # Risk engine notes the error
    risk = calculate_risk(
        diff="",
        validated_findings=[],
        conflicts=[],
        linter_results=[{"tool": "ruff", "raw_output": out}],
        changed_files=["foo.py"],
        additions=0,
        deletions=0,
    )
    assert any("Linter execution errors" in r for r in risk.factors["code_complexity"]["reasons"])


def test_failed_tool_execution_preserves_error_signal():
    """Verify non-zero error exit codes or timeouts are preserved as error signals."""
    bandit = BanditLinter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="Bandit syntax error")
        out = bandit.execute("/tmp/test", ["bad.py"])

    assert out["status"] == "error"
    assert out["error_type"] == "execution_failed"
    assert out["results"] == []

    risk = calculate_risk(
        diff="",
        validated_findings=[],
        conflicts=[],
        linter_results=[{"tool": "bandit", "raw_output": out}],
        changed_files=["bad.py"],
        additions=0,
        deletions=0,
    )
    reasons = risk.factors["code_complexity"]["reasons"]
    assert any("Linter execution errors" in r and "bandit: execution_failed" in r for r in reasons)
