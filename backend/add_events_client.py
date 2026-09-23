import re

file_path = 'backend/app/github/client.py'
with open(file_path, 'r') as f:
    content = f.read()

events_method = """
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
"""

content = content.replace("    def get_pull_request_checks(", events_method + "\n    def get_pull_request_checks(")

with open(file_path, 'w') as f:
    f.write(content)
