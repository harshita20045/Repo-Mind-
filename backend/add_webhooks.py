import re

file_path = 'backend/app/github/client.py'
with open(file_path, 'r') as f:
    content = f.read()

webhook_logic = """
    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def register_webhook(self, owner: str, repo: str, webhook_url: str, webhook_secret: str) -> Dict[str, Any]:
        \"\"\"
        Register a webhook for the repository.
        Requires admin:repo_hook permissions.
        \"\"\"
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
"""

content = content.replace("    # ------------------------------------------------------------------\n    # Pull requests", webhook_logic + "\n    # ------------------------------------------------------------------\n    # Pull requests")

with open(file_path, 'w') as f:
    f.write(content)


service_path = 'backend/app/github/service.py'
with open(service_path, 'r') as f:
    service = f.read()

webhook_setup = """
    github_repository_id = str(repo_meta.get("id"))
    default_branch_actual = repo_meta.get("default_branch", default_branch)

    # Register webhook
    from backend.app.core.config import settings
    webhook_url = getattr(settings, "GITHUB_WEBHOOK_URL", None)
    webhook_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
    
    if webhook_url and webhook_secret:
        try:
            client.register_webhook(github_owner, github_name, webhook_url, webhook_secret)
        except GitHubAPIError as e:
            # We don't fail the entire repository connection if webhook fails,
            # but we could log it or set a status
            pass
"""

service = service.replace("    github_repository_id = str(repo_meta.get(\"id\"))\n    default_branch_actual = repo_meta.get(\"default_branch\", default_branch)", webhook_setup)

with open(service_path, 'w') as f:
    f.write(service)
