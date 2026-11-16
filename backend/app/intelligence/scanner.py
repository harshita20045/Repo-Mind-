import os
import re
from typing import Dict, List, Set, Any, Optional

EXCLUDED_DIRS = {
    "node_modules",
    "vendor",
    "generated",
    ".git",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".idea",
    ".vscode",
    "coverage",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".turbo",
}

EXCLUDED_FILES = {
    ".env",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}

EXCLUDED_EXTENSIONS = {
    ".pem", ".key", ".p12", ".pfx",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp",
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".pyc",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".mov", ".avi",
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".java": "Java",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
}

KNOWN_ENTRY_FILENAMES = {
    "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py", "server.py",
    "index.js", "index.ts", "server.js", "server.ts", "main.js", "main.ts",
    "main.go", "main.rs", "App.jsx", "App.tsx", "main.jsx", "main.tsx",
}

KNOWN_CONFIG_FILENAMES = {
    "docker-compose.yml", "docker-compose.yaml", "dockerfile", "containerfile",
    ".env.example", ".env.sample", ".env.template",
    "tsconfig.json", "jsconfig.json", "vite.config.js", "vite.config.ts",
    "alembic.ini", "pyproject.toml", "requirements.txt", "package.json",
    "cargo.toml", "go.mod", "pom.xml", "build.gradle", "webpack.config.js",
    "tailwind.config.js", "postcss.config.js", "eslint.config.js", ".eslintrc.json",
}


class RepositoryScanner:
    """
    Module 1: Repository Scanner
    Scans repository directory structure, identifies languages, frameworks,
    entry points, config files, routes, database models, and service layers
    while enforcing strict security exclusions.
    """

    def __init__(self):
        pass

    def should_exclude(self, file_path: str) -> bool:
        """Determines if a path should be excluded based on directory, file name or extension."""
        clean_path = file_path.replace("\\", "/")
        parts = clean_path.split("/")
        
        # Check parent directory names
        for part in parts[:-1]:
            if part in EXCLUDED_DIRS or part.startswith("."):
                if part not in (".github", ".agents"):
                    return True

        filename = parts[-1].lower()
        
        if filename in EXCLUDED_FILES or (filename.startswith(".env") and not filename.endswith((".example", ".sample", ".template"))):
            return True

        for ext in EXCLUDED_EXTENSIONS:
            if filename.endswith(ext):
                return True

        return False

    def scan_files(self, file_dict: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyzes a repository represented as a dict of {relative_path: content_string}.
        Extracts structural intelligence without running any untrusted code.
        """
        languages_count: Dict[str, int] = {}
        languages_lines: Dict[str, int] = {}
        entry_points: List[str] = []
        config_files: List[str] = []
        api_route_files: List[str] = []
        db_model_files: List[str] = []
        service_files: List[str] = []
        documentation_files: List[str] = []
        frameworks: Set[str] = set()

        total_files = 0
        total_lines = 0

        for path, content in file_dict.items():
            clean_path = path.replace("\\", "/")
            if self.should_exclude(clean_path):
                continue

            total_files += 1
            filename = clean_path.split("/")[-1].lower()
            ext = os.path.splitext(filename)[1].lower()

            # Count lines
            line_count = len(content.splitlines()) if content else 0
            total_lines += line_count

            # Language classification
            lang = LANGUAGE_EXTENSIONS.get(ext)
            if lang:
                languages_count[lang] = languages_count.get(lang, 0) + 1
                languages_lines[lang] = languages_lines.get(lang, 0) + line_count

            # Entry points
            if filename in KNOWN_ENTRY_FILENAMES or 'if __name__ == "__main__":' in content:
                entry_points.append(clean_path)

            # Configuration files
            if filename in KNOWN_CONFIG_FILENAMES:
                config_files.append(clean_path)

            # Documentation files
            if ext in (".md", ".rst", ".txt") and any(k in filename for k in ("readme", "doc", "adr", "contributing", "guide", "spec")):
                documentation_files.append(clean_path)

            # Inspect content signatures for frameworks and roles
            lower_content = content.lower() if content else ""

            # Framework detection
            if "fastapi" in lower_content or "from fastapi" in content:
                frameworks.add("FastAPI")
            if "from flask import" in content or "import flask" in content:
                frameworks.add("Flask")
            if "django.db" in content or "django.core" in content or "from django" in content:
                frameworks.add("Django")
            if "from sqlalchemy" in content or "import sqlalchemy" in content:
                frameworks.add("SQLAlchemy")
            if "import react" in lower_content or 'from "react"' in content or "from 'react'" in content:
                frameworks.add("React")
            if "from 'next'" in content or 'from "next"' in content:
                frameworks.add("Next.js")
            if "from 'vue'" in content or 'from "vue"' in content:
                frameworks.add("Vue")
            if "from 'express'" in content or 'require("express")' in content or "require('express')" in content:
                frameworks.add("Express")
            if "tailwindcss" in lower_content or "@tailwind" in content:
                frameworks.add("Tailwind CSS")
            if "pytest" in lower_content or "import pytest" in content:
                frameworks.add("Pytest")
            if "alembic" in lower_content or "from alembic" in content:
                frameworks.add("Alembic")
            if "prisma" in lower_content:
                frameworks.add("Prisma")

            # Route detection signatures
            if any(p in content for p in ("@app.get", "@app.post", "@router.get", "@router.post", "@app.route", "app.get(", "router.get(")):
                api_route_files.append(clean_path)

            # Database model signatures
            if any(p in content for p in ("(Base)", "models.Model", "declarative_base", "class ")) and any(m in content for m in ("Column(", "db.Column", "models.Char", "PrimaryKeyConstraint")):
                db_model_files.append(clean_path)

            # Service layer signatures
            if any(part in clean_path.lower() for part in ("/services/", "/service.", "/controllers/", "/managers/")):
                service_files.append(clean_path)

        # Determine primary language
        primary_language = None
        if languages_lines:
            primary_language = max(languages_lines, key=languages_lines.get)
        elif languages_count:
            primary_language = max(languages_count, key=languages_count.get)

        return {
            "primary_language": primary_language,
            "languages": {
                "file_counts": languages_count,
                "line_counts": languages_lines,
            },
            "frameworks": sorted(list(frameworks)),
            "entry_points": sorted(entry_points),
            "config_files": sorted(config_files),
            "api_route_files": sorted(api_route_files),
            "db_model_files": sorted(db_model_files),
            "service_files": sorted(service_files),
            "documentation_files": sorted(documentation_files),
            "stats": {
                "total_files": total_files,
                "total_lines": total_lines,
                "code_files_count": sum(c for l, c in languages_count.items() if l not in ("Markdown", "reStructuredText", "JSON", "YAML", "TOML")),
                "doc_files_count": len(documentation_files),
            }
        }
