import os
import re
from typing import Dict, Any, List, Optional


class DocMetadata:
    def __init__(
        self,
        file_path: str,
        category: str,
        title: str,
        summary: str,
        headings: List[str],
        importance_weight: float = 1.0,
    ):
        self.file_path = file_path
        self.category = category  # readme, architecture, adr, api_doc, coding_standards, technical_doc, general_doc
        self.title = title
        self.summary = summary
        self.headings = headings
        self.importance_weight = importance_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "headings": self.headings,
            "importance_weight": self.importance_weight,
        }


class DocumentationIntelligence:
    """
    Module 3: Documentation Intelligence
    Discovers, classifies, and indexes READMEs, architecture specs,
    ADRs, coding standards, and API documentation with semantic categories.
    """

    def is_documentation_file(self, file_path: str) -> bool:
        clean = file_path.replace("\\", "/").lower()
        ext = os.path.splitext(clean)[1]
        if ext in (".md", ".rst", ".txt"):
            return True
        if ext in (".json", ".yaml", ".yml") and any(k in clean for k in ("openapi", "swagger")):
            return True
        return False

    def classify_and_extract(self, file_path: str, content: str) -> Optional[DocMetadata]:
        clean = file_path.replace("\\", "/").lower()
        filename = clean.split("/")[-1]

        if not self.is_documentation_file(file_path):
            return None

        # Determine Category
        category = "general_doc"
        importance = 1.0

        if "readme" in filename:
            category = "readme"
            importance = 1.5
        elif any(k in clean for k in ("/adr/", "/adrs/", "adr-")) or re.search(r"/\d{3,4}-.+\.md", clean):
            category = "adr"
            importance = 1.3
        elif any(k in clean for k in ("architecture", "design", "blueprint", "system_design")):
            category = "architecture"
            importance = 1.4
        elif any(k in clean for k in ("contributing", "coding_standard", "styleguide", "guideline", "gemini.md")):
            category = "coding_standards"
            importance = 1.2
        elif any(k in clean for k in ("openapi", "swagger", "api_doc", "api.md", "/api/")):
            category = "api_doc"
            importance = 1.3
        elif any(k in clean for k in ("setup", "install", "deploy", "security", "database", "audit", "roadmap")):
            category = "technical_doc"
            importance = 1.1

        # Extract title and headings
        title = filename
        headings = []
        lines = content.splitlines() if content else []
        for line in lines:
            sline = line.strip()
            if sline.startswith("# ") and title == filename:
                title = sline.lstrip("# ").strip()
            elif sline.startswith(("#", "##", "###")):
                headings.append(sline.lstrip("#").strip())

        # Generate brief summary from first non-heading paragraph
        summary_paragraphs = []
        for line in lines:
            sline = line.strip()
            if sline and not sline.startswith("#") and not sline.startswith("```"):
                summary_paragraphs.append(sline)
                if len(" ".join(summary_paragraphs)) >= 200:
                    break
        summary = " ".join(summary_paragraphs)[:300] if summary_paragraphs else title

        return DocMetadata(
            file_path=file_path,
            category=category,
            title=title,
            summary=summary,
            headings=headings[:15],
            importance_weight=importance,
        )
