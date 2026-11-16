from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CodeSymbolSchema(BaseModel):
    name: str
    symbol_type: str  # class, function, method, interface, api_endpoint, db_model
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_symbol: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PackageDependencySchema(BaseModel):
    ecosystem: str
    package_name: str
    version_spec: Optional[str] = None
    is_dev: bool = False
    file_path: Optional[str] = None


class GraphNodeSchema(BaseModel):
    id: int
    node_key: str
    node_type: str
    name: str
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class GraphEdgeSchema(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    relation_type: str
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    total_nodes: int
    total_edges: int


class RepositoryScanSummaryResponse(BaseModel):
    repository_id: int
    primary_language: Optional[str] = None
    languages: Dict[str, Any] = Field(default_factory=dict)
    frameworks: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
    architecture_summary: Optional[str] = None
    mermaid_diagram: Optional[str] = None
    scanned_commit_sha: Optional[str] = None
    updated_at: Optional[datetime] = None


class IndexingTriggerResponse(BaseModel):
    message: str
    repository_id: int
    status: str
    scanned_files_count: int
    symbols_extracted_count: int
    dependencies_count: int
