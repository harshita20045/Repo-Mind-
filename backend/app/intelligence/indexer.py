import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.organizations.models import Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.rag.embedder import LocalEmbedder
from backend.app.rag.ast_chunker import ASTCodeChunker
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    PackageDependency,
    RepositoryScanSummary,
)
from backend.app.intelligence.scanner import RepositoryScanner
from backend.app.intelligence.parser import LanguageAwareParser, ParsedCodeFile
from backend.app.intelligence.documentation import DocumentationIntelligence
from backend.app.intelligence.dependencies import DependencyExtractor
from backend.app.intelligence.graph import CodeKnowledgeGraph

logger = logging.getLogger("repomind.intelligence")


class RepositoryIndexer:
    """
    Module 6: Incremental Repository Intelligence Indexer
    Orchestrates repository scanning, AST parsing, dependency extraction,
    knowledge graph generation, documentation intelligence, and syntax-aware RAG embedding.
    Supports incremental diffing against content hashes to minimize computation.
    """

    def __init__(self, db: Session, repository_id: int):
        self.db = db
        self.repository_id = repository_id
        self.scanner = RepositoryScanner()
        self.parser = LanguageAwareParser()
        self.doc_intel = DocumentationIntelligence()
        self.dep_extractor = DependencyExtractor()
        self.chunker = ASTCodeChunker()
        self.embedder = LocalEmbedder()

    def index_from_file_dict(
        self,
        file_dict: Dict[str, str],
        commit_sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Indexes a repository provided as a dictionary of {file_path: content_string}.
        Performs incremental diffing: detects added, modified, deleted, and unchanged files.
        """
        repo = self.db.get(Repository, self.repository_id)
        if not repo:
            raise ValueError(f"Repository {self.repository_id} not found")

        # Filter out excluded files upfront
        valid_files = {
            path.replace("\\", "/"): content
            for path, content in file_dict.items()
            if not self.scanner.should_exclude(path)
        }

        # 1. Fetch existing indexed documents for diffing
        existing_docs = {
            doc.path: doc
            for doc in self.db.execute(
                select(Document).where(Document.repository_id == self.repository_id)
            ).scalars().all()
        }

        added_paths: Set[str] = set()
        modified_paths: Set[str] = set()
        unchanged_paths: Set[str] = set()
        current_hashes: Dict[str, str] = {}

        for path, content in valid_files.items():
            chash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            current_hashes[path] = chash

            if path not in existing_docs:
                added_paths.add(path)
            elif existing_docs[path].content_hash != chash:
                modified_paths.add(path)
            else:
                unchanged_paths.add(path)

        deleted_paths = set(existing_docs.keys()) - set(valid_files.keys())

        logger.info(
            "Repo %d incremental diff: %d added, %d modified, %d deleted, %d unchanged",
            self.repository_id,
            len(added_paths),
            len(modified_paths),
            len(deleted_paths),
            len(unchanged_paths),
        )

        # 2. Clean up deleted and modified files from RAG
        for del_path in deleted_paths:
            self.db.execute(
                delete(Document).where(
                    Document.repository_id == self.repository_id,
                    Document.path == del_path,
                )
            )

        for mod_path in modified_paths:
            # Purge existing chunks for modified document
            doc = existing_docs[mod_path]
            self.db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.repository_id == self.repository_id,
                    DocumentChunk.document_id == doc.id,
                )
            )
            doc.content_hash = current_hashes[mod_path]
            doc.updated_at = datetime.now(timezone.utc)

        # Insert records for newly added files
        for add_path in added_paths:
            new_doc = Document(
                repository_id=self.repository_id,
                path=add_path,
                content_hash=current_hashes[add_path],
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(new_doc)
            existing_docs[add_path] = new_doc

        self.db.flush()

        # 3. Parse AST for ALL current code files to build complete knowledge graph
        parsed_files: List[ParsedCodeFile] = []
        for path, content in valid_files.items():
            parsed = self.parser.parse_file(path, content)
            parsed_files.append(parsed)

        # 4. Extract Package Dependencies
        dependencies = self.dep_extractor.extract_from_manifests(valid_files)
        # Purge existing dependencies
        self.db.execute(
            delete(PackageDependency).where(
                PackageDependency.repository_id == self.repository_id
            )
        )
        for dep in dependencies:
            self.db.add(PackageDependency(
                repository_id=self.repository_id,
                ecosystem=dep.ecosystem,
                package_name=dep.package_name,
                version_spec=dep.version_spec,
                is_dev=dep.is_dev,
                file_path=dep.file_path,
            ))
        self.db.flush()

        # 5. Build and Persist Code Knowledge Graph
        graph = CodeKnowledgeGraph(self.repository_id)
        graph.build_from_parsed_files(parsed_files)
        node_count, edge_count = graph.persist(self.db)
        mermaid_diagram = graph.generate_mermaid_diagram()

        # 6. Re-index chunks ONLY for added and modified files
        files_to_chunk = added_paths | modified_paths
        total_chunks_created = 0

        for path in files_to_chunk:
            content = valid_files[path]
            doc = existing_docs[path]
            parsed_entry = next((pf for pf in parsed_files if pf.file_path == path), None)

            # Determine whether file is code or documentation
            if self.doc_intel.is_documentation_file(path):
                chunks = self.chunker.chunk_documentation(path, content)
            else:
                chunks = self.chunker.chunk_parsed_code(path, content, parsed_entry)

            if not chunks:
                continue

            # Embed chunks
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embedder.embed_chunks(chunk_texts)

            # Save chunks
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    repository_id=self.repository_id,
                    text=chunk.text,
                    embedding=emb,
                    chunk_index=idx,
                    chunk_type=chunk.chunk_type,
                    file_path=path,
                )
                self.db.add(db_chunk)
                total_chunks_created += 1

        self.db.flush()

        # 7. Generate Repository Scanner Summary
        scan_results = self.scanner.scan_files(valid_files)
        summary = (
            f"Repository primary language: {scan_results.get('primary_language', 'Unknown')}. "
            f"Identified frameworks: {', '.join(scan_results.get('frameworks', [])) or 'None'}. "
            f"Total indexed files: {len(valid_files)}, symbols: {node_count}, graph edges: {edge_count}."
        )

        # Update or create RepositoryScanSummary
        existing_summary = self.db.execute(
            select(RepositoryScanSummary).where(
                RepositoryScanSummary.repository_id == self.repository_id
            )
        ).scalar_one_or_none()

        if existing_summary:
            existing_summary.primary_language = scan_results.get("primary_language")
            existing_summary.languages = scan_results.get("languages")
            existing_summary.frameworks = scan_results.get("frameworks")
            existing_summary.entry_points = scan_results.get("entry_points")
            existing_summary.stats = {
                **scan_results.get("stats", {}),
                "nodes_count": node_count,
                "edges_count": edge_count,
                "dependencies_count": len(dependencies),
            }
            existing_summary.architecture_summary = summary
            existing_summary.mermaid_diagram = mermaid_diagram
            existing_summary.scanned_commit_sha = commit_sha
            existing_summary.updated_at = datetime.now(timezone.utc)
        else:
            new_summary = RepositoryScanSummary(
                repository_id=self.repository_id,
                primary_language=scan_results.get("primary_language"),
                languages=scan_results.get("languages"),
                frameworks=scan_results.get("frameworks"),
                entry_points=scan_results.get("entry_points"),
                stats={
                    **scan_results.get("stats", {}),
                    "nodes_count": node_count,
                    "edges_count": edge_count,
                    "dependencies_count": len(dependencies),
                },
                architecture_summary=summary,
                mermaid_diagram=mermaid_diagram,
                scanned_commit_sha=commit_sha,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(new_summary)

        # 8. Mark repository status as indexed
        repo.index_status = "indexed"
        repo.last_indexed_at = datetime.now(timezone.utc)

        self.db.commit()

        return {
            "repository_id": self.repository_id,
            "status": "indexed",
            "files_scanned": len(valid_files),
            "added_files": len(added_paths),
            "modified_files": len(modified_paths),
            "deleted_files": len(deleted_paths),
            "unchanged_files": len(unchanged_paths),
            "symbols_count": node_count,
            "edges_count": edge_count,
            "dependencies_count": len(dependencies),
            "chunks_created": total_chunks_created,
            "primary_language": scan_results.get("primary_language"),
            "frameworks": scan_results.get("frameworks"),
        }
