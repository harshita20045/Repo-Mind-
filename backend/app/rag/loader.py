import hashlib
from typing import List, Iterator, Dict
from backend.app.github.client import GitHubClient, GitHubAPIError

# Exact exclusions required by the approved Phase 6 security boundary
EXCLUDED_DIRS = {
    "node_modules",
    "vendor",
    "generated",
    ".git",
    "dist",
    "build",
    ".venv",
    "__pycache__",
}

EXCLUDED_FILES = {
    ".env",
    "package-lock.json",
    "yarn.lock",
}

EXCLUDED_EXTENSIONS = {
    ".pem",
    ".key",
    ".zip",
    ".tar",
    ".gz",
    ".jpg",
    ".png",
    ".svg",
}

SUPPORTED_EXTENSIONS = {
    # Docs
    ".md", ".txt", ".rst",
    # Python
    ".py",
    # JavaScript / TypeScript
    ".js", ".jsx", ".ts", ".tsx",
    # Java
    ".java",
    # Go
    ".go",
    # C/C++
    ".c", ".cpp", ".h", ".hpp",
    # Config / Structured
    ".json", ".yaml", ".yml", ".toml",
}

class DocumentLoader:
    """
    Discovers and loads documents from a GitHub repository using the GitHub API.
    Enforces deterministic filtering and security exclusions for Code-Aware RAG.
    """
    def __init__(self, github_client: GitHubClient, owner: str, repo: str, sha: str):
        self.client = github_client
        self.owner = owner
        self.repo = repo
        self.sha = sha

    def _should_exclude_path(self, path: str) -> bool:
        """Deterministically determine if a path should be excluded based on security rules."""
        parts = path.split("/")
        
        # Check excluded directories
        for part in parts[:-1]:
            if part in EXCLUDED_DIRS:
                return True
                
        filename = parts[-1]
        
        # Check exact filename exclusions
        if filename in EXCLUDED_FILES or filename.startswith(".env."):
            return True
            
        # Check extension exclusions
        for ext in EXCLUDED_EXTENSIONS:
            if filename.endswith(ext):
                return True
                
        # Must be a supported extension
        if not any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            return True
            
        return False
        
    def determine_chunk_type(self, path: str) -> str:
        """Categorize the file for RAG routing."""
        filename = path.split("/")[-1].lower()
        if filename.endswith((".md", ".txt", ".rst")):
            return "documentation"
        if "test" in path.lower() or "spec" in path.lower():
            return "test_code"
        return "source_code"

    def discover_documents(self) -> List[Dict[str, str]]:
        """
        Fetch the recursive Git tree and return a list of metadata dicts for files to index.
        Fails safely if the tree is truncated by GitHub API limits.
        """
        tree_data = self.client.get_repository_tree(self.owner, self.repo, self.sha, recursive=True)
        
        if tree_data.get("truncated", False):
            raise GitHubAPIError(
                403, "Repository tree is truncated by GitHub API limits. Cannot safely index incomplete repository."
            )
            
        documents = []
        for item in tree_data.get("tree", []):
            if item.get("type") != "blob":
                continue
                
            path = item.get("path", "")
            if not self._should_exclude_path(path):
                documents.append({
                    "path": path,
                    "sha": item.get("sha", "")
                })
                
        # Deterministic sorting
        documents.sort(key=lambda x: x["path"])
        return documents

    def load_document_content(self, path: str, file_sha: str) -> str:
        """
        Fetch the content of a document and decode it.
        Skips invalid UTF-8 files safely.
        """
        raw_content = self.client.get_blob_content(self.owner, self.repo, file_sha)
        try:
            return raw_content.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    def hash_content(self, content: str) -> str:
        """Compute deterministic SHA-256 hash of the content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
