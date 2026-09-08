"""
GitHub API client — Phase 5.

Pure adapter: zero AI dependencies per ADR-010.
Uses httpx for HTTP and a read-only PAT for authentication.

Token security:
- The PAT is NEVER logged, returned in API responses, or included in exceptions.
- It is decrypted in-process only when needed to make a GitHub API call.
"""
import httpx
from typing import Any, Dict, List, Optional


GITHUB_API_BASE = "https://api.github.com"
_DEFAULT_TIMEOUT = 30  # seconds


class GitHubAPIError(Exception):
    """Raised for non-retryable GitHub API errors (e.g. 401, 403, 404)."""
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API error {status_code}: {message}")


class GitHubTransientError(Exception):
    """Raised for transient errors (5xx) that should be retried once."""
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API transient error {status_code} — retry once")


class GitHubClient:
    """
    Thin httpx wrapper for the GitHub REST API.

    Usage:
        client = GitHubClient(pat)          # PAT stays in memory only
        prs = client.list_pull_requests(owner, repo)
    """

    def __init__(self, pat: str) -> None:
        # Token is kept private; never surfaced in repr or str
        self._headers = {
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request and return parsed JSON. Raises on error."""
        url = f"{GITHUB_API_BASE}{path}"
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.get(url, headers=self._headers, params=params)

        if response.status_code in (401, 403, 404):
            raise GitHubAPIError(response.status_code, response.text[:200])
        if response.status_code == 429:
            raise GitHubAPIError(429, "Rate limit exceeded")
        if response.status_code >= 500:
            raise GitHubTransientError(response.status_code)
        if not response.is_success:
            raise GitHubAPIError(response.status_code, response.text[:200])

        return response.json()

    # ------------------------------------------------------------------
    # Repository validation
    # ------------------------------------------------------------------

    def validate_repository_access(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Verify the PAT can access the repository.
        Returns repository metadata on success; raises GitHubAPIError otherwise.
        """
        return self._get(f"/repos/{owner}/{repo}")

    # ------------------------------------------------------------------
    # Pull requests
    # ------------------------------------------------------------------

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 50,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        return self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page, "page": page},
        )

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> Dict[str, Any]:
        """Fetch a single pull request by number."""
        return self._get(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    def get_pull_request_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> str:
        """
        Fetch the unified diff for a pull request.
        Uses the application/vnd.github.v3.diff Accept header.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
        diff_headers = {**self._headers, "Accept": "application/vnd.github.v3.diff"}
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.get(url, headers=diff_headers)

        if not response.is_success:
            raise GitHubAPIError(response.status_code, "Failed to fetch PR diff")
        return response.text

    def list_pull_request_commits(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> List[Dict[str, Any]]:
        """List commits on a pull request (for re-analysis diffing)."""
        return self._get(f"/repos/{owner}/{repo}/pulls/{pr_number}/commits")

    # ------------------------------------------------------------------
    # Repository documentation discovery (Phase 6/7 — RAG)
    # ------------------------------------------------------------------

    def get_repository_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> Any:
        """
        List directory contents or fetch a single file.
        Returns a list of items (directory) or a dict (file) per GitHub API.
        """
        params = {}
        if ref:
            params["ref"] = ref
        return self._get(f"/repos/{owner}/{repo}/contents/{path}", params=params or None)
