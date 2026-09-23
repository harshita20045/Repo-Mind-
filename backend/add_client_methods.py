import re

file_path = 'backend/app/github/client.py'
with open(file_path, 'r') as f:
    content = f.read()

new_methods = """
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
        
    def get_pull_request_checks(
        self,
        owner: str,
        repo: str,
        head_sha: str,
    ) -> Dict[str, Any]:
        return self._get(
            f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs",
        )
"""

content = content.replace("    # ------------------------------------------------------------------\n    # Repository documentation", new_methods + "\n    # ------------------------------------------------------------------\n    # Repository documentation")

with open(file_path, 'w') as f:
    f.write(content)
