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
    # Automation Actions (Phase 15/16)
    # ------------------------------------------------------------------

    def submit_pull_request_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        event: str,
        body: str = "",
    ) -> Dict[str, Any]:
        """
        Submit a review (APPROVE or REQUEST_CHANGES).
        Requires Pull/Push access (repo scope).
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_id,
            "event": event,
        }
        if body:
            payload["body"] = body

        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.post(url, headers=self._headers, json=payload)

        if response.status_code in (401, 403, 404):
            raise GitHubAPIError(response.status_code, "Failed to submit review. Check permissions.")
        elif response.status_code == 422:
            raise GitHubAPIError(response.status_code, "Unprocessable Entity (e.g., stale commit_sha or already approved).")
        elif not response.is_success:
            raise GitHubAPIError(response.status_code, response.text[:200])

        return response.json()

    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        sha: str,
        commit_title: str = "",
        commit_message: str = "",
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """
        Merge a PR. SHA-safe.
        Requires Contents: Write & PRs: Write.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        payload = {
            "sha": sha,
            "merge_method": merge_method,
        }
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message

        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.put(url, headers=self._headers, json=payload)

        if response.status_code in (405, 409):
            raise GitHubAPIError(response.status_code, "Merge conflict or not mergeable.")
        elif response.status_code == 422:
            raise GitHubAPIError(422, "SHA mismatch (PR head has moved) or validation failed.")
        elif response.status_code in (401, 403, 404):
            raise GitHubAPIError(response.status_code, "Failed to merge PR. Check permissions.")
        elif not response.is_success:
            raise GitHubAPIError(response.status_code, response.text[:200])

        return response.json()

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def register_webhook(self, owner: str, repo: str, webhook_url: str, webhook_secret: str) -> Dict[str, Any]:
        """
        Register a webhook for the repository.
        Requires admin:repo_hook permissions.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/hooks"
        payload = {
            "name": "web",
            "active": True,
            "events": [
                "pull_request",
                "pull_request_review",
                "pull_request_review_comment",
                "push",
                "issue_comment"
            ],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": webhook_secret,
                "insecure_ssl": "0"
            }
        }
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.post(url, headers=self._headers, json=payload)

        if response.status_code == 422:
            # Check if it already exists, GitHub returns 422 if hook already exists
            # We can just ignore or try to find and update it
            pass
        elif response.status_code in (401, 403, 404):
            raise GitHubAPIError(response.status_code, "Failed to create webhook. Check permissions.")
        elif not response.is_success:
            raise GitHubAPIError(response.status_code, response.text[:200])

        return response.json() if response.is_success else {}

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

    def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        List files modified/added/renamed/deleted in a pull request.
        Returns metadata including file path, status, and contents_url/sha.
        """
        return self._get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
            params={"per_page": per_page, "page": page},
        )


    def list_pull_request_reviews(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        return self._get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            params={"per_page": per_page, "page": page},
        )

    def list_pull_request_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        return self._get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
            params={"per_page": per_page, "page": page},
        )
        

    def list_pull_request_events(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        return self._get(
            f"/repos/{owner}/{repo}/issues/{pr_number}/events",
            params={"per_page": per_page, "page": page},
        )

    def get_pull_request_checks(
        self,
        owner: str,
        repo: str,
        head_sha: str,
    ) -> Dict[str, Any]:
        return self._get(
            f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs",
        )

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

    def get_repository_tree(self, owner: str, repo: str, sha: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Fetch the Git tree for a repository, optionally recursively.
        Returns the tree structure to avoid rate limits of the contents API.
        """
        params = {}
        if recursive:
            params["recursive"] = "1"
        return self._get(f"/repos/{owner}/{repo}/git/trees/{sha}", params=params or None)

    def get_blob_content(self, owner: str, repo: str, sha: str) -> bytes:
        """
        Fetch the raw content of a Git blob (file) by its SHA.
        Returns the raw bytes since the file might be binary or UTF-8.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/blobs/{sha}"
        headers = {**self._headers, "Accept": "application/vnd.github.v3.raw"}
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as http:
            response = http.get(url, headers=headers)

        if response.status_code in (401, 403, 404):
            raise GitHubAPIError(response.status_code, response.text[:200])
        if response.status_code == 429:
            raise GitHubAPIError(429, "Rate limit exceeded")
        if response.status_code >= 500:
            raise GitHubTransientError(response.status_code)
        if not response.is_success:
            raise GitHubAPIError(response.status_code, "Failed to fetch blob content")

        return response.content
