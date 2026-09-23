import re

file_path = 'backend/app/github/client.py'
with open(file_path, 'r') as f:
    content = f.read()

automation_methods = """
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
        \"\"\"
        Submit a review (APPROVE or REQUEST_CHANGES).
        Requires Pull/Push access (repo scope).
        \"\"\"
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
        \"\"\"
        Merge a PR. SHA-safe.
        Requires Contents: Write & PRs: Write.
        \"\"\"
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
"""

content = content.replace("    # ------------------------------------------------------------------\n    # Webhooks", automation_methods + "\n    # ------------------------------------------------------------------\n    # Webhooks")

with open(file_path, 'w') as f:
    f.write(content)
