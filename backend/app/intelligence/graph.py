from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.intelligence.parser import ParsedCodeFile, CodeSymbol


class CodeKnowledgeGraph:
    """
    Module 4: Code Knowledge Graph
    Constructs, queries, and serializes cross-file relationship graphs between
    files, modules, classes, functions, API endpoints, services, and database models.
    """

    def __init__(self, repository_id: int):
        self.repository_id = repository_id
        self.graph = nx.DiGraph()
        self.node_metadata: Dict[str, Dict[str, Any]] = {}

    def add_node(
        self,
        node_key: str,
        node_type: str,
        name: str,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.graph.add_node(
            node_key,
            node_type=node_type,
            name=name,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
        )
        self.node_metadata[node_key] = metadata or {}

    def add_edge(
        self,
        source_key: str,
        target_key: str,
        relation_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if source_key in self.graph and target_key in self.graph:
            self.graph.add_edge(
                source_key,
                target_key,
                relation_type=relation_type,
                weight=weight,
                metadata=metadata or {},
            )

    def build_from_parsed_files(self, parsed_files: List[ParsedCodeFile]) -> None:
        """Constructs graph nodes and relationships from parsed code files."""
        # 1. Register Modules and Files
        modules_seen: Set[str] = set()
        file_keys: Dict[str, str] = {}  # clean_path -> file_node_key

        for pf in parsed_files:
            clean_path = pf.file_path.replace("\\", "/")
            file_key = f"file:{clean_path}"
            file_keys[clean_path] = file_key

            # Module / Directory
            parts = clean_path.split("/")
            if len(parts) > 1:
                mod_name = "/".join(parts[:-1])
                mod_key = f"mod:{mod_name}"
                if mod_key not in modules_seen:
                    modules_seen.add(mod_key)
                    self.add_node(
                        node_key=mod_key,
                        node_type="module",
                        name=mod_name,
                        file_path=mod_name,
                    )
                # Module contains File
                self.add_node(
                    node_key=file_key,
                    node_type="file",
                    name=parts[-1],
                    file_path=clean_path,
                )
                self.add_edge(mod_key, file_key, relation_type="contains")
            else:
                self.add_node(
                    node_key=file_key,
                    node_type="file",
                    name=parts[0],
                    file_path=clean_path,
                )

        # 2. Register Symbols (Classes, Functions, Methods, API Routes, DB Models)
        symbol_key_map: Dict[str, str] = {}  # (clean_path, symbol_name) -> symbol_key

        for pf in parsed_files:
            clean_path = pf.file_path.replace("\\", "/")
            file_key = file_keys.get(clean_path, f"file:{clean_path}")

            for sym in pf.symbols:
                if sym.symbol_type == "class":
                    sym_key = f"class:{clean_path}:{sym.name}"
                elif sym.symbol_type == "db_model":
                    sym_key = f"model:{clean_path}:{sym.name}"
                elif sym.symbol_type == "method":
                    sym_key = f"method:{clean_path}:{sym.parent_symbol}.{sym.name}"
                elif sym.symbol_type == "api_endpoint":
                    api_info = sym.metadata.get("api_route") or {}
                    method = api_info.get("method", "ROUTE")
                    path = api_info.get("path", sym.name)
                    sym_key = f"api:{method}:{path}"
                else:
                    sym_key = f"fn:{clean_path}:{sym.name}"

                symbol_key_map[(clean_path, sym.name)] = sym_key
                self.add_node(
                    node_key=sym_key,
                    node_type=sym.symbol_type,
                    name=sym.name,
                    file_path=clean_path,
                    start_line=sym.start_line,
                    end_line=sym.end_line,
                    metadata=sym.metadata,
                )

                # File contains Symbol
                self.add_edge(file_key, sym_key, relation_type="contains")

                # If method, Class contains Method
                if sym.parent_symbol:
                    class_key = symbol_key_map.get((clean_path, sym.parent_symbol))
                    if class_key:
                        self.add_edge(class_key, sym_key, relation_type="contains")

            # 3. Register API Endpoint Exposes
            for api_def in pf.api_definitions:
                api_key = f"api:{api_def['method']}:{api_def['path']}"
                if api_key in self.graph:
                    fn_key = symbol_key_map.get((clean_path, api_def["handler"]))
                    if fn_key:
                        self.add_edge(api_key, fn_key, relation_type="exposes")

        # 4. Resolve Imports (File -> Module/File)
        for pf in parsed_files:
            clean_path = pf.file_path.replace("\\", "/")
            src_file_key = file_keys.get(clean_path)
            if not src_file_key:
                continue

            for imp in pf.imports:
                mod = imp.get("module", "")
                if mod:
                    # Check if imported module matches an internal file
                    mod_path = mod.replace(".", "/")
                    target_file = None
                    for candidate_path, cand_key in file_keys.items():
                        if candidate_path.startswith(mod_path) or mod_path in candidate_path:
                            target_file = cand_key
                            break
                    if target_file and target_file != src_file_key:
                        self.add_edge(src_file_key, target_file, relation_type="imports")

        # 5. Resolve Calls (Function -> Function)
        for pf in parsed_files:
            clean_path = pf.file_path.replace("\\", "/")
            for call in pf.calls:
                callee_name = call.get("callee")
                if not callee_name:
                    continue

                # Find matching target symbol
                target_key = symbol_key_map.get((clean_path, callee_name))
                if not target_key:
                    # Cross-file search
                    for (cp, sn), k in symbol_key_map.items():
                        if sn == callee_name:
                            target_key = k
                            break

                if target_key:
                    # Find which symbol made the call based on line number
                    call_line = call.get("line", 0)
                    caller_key = None
                    for sym in pf.symbols:
                        if sym.start_line and sym.end_line and sym.start_line <= call_line <= sym.end_line:
                            caller_key = symbol_key_map.get((clean_path, sym.name))
                            break

                    if caller_key and caller_key != target_key:
                        self.add_edge(caller_key, target_key, relation_type="calls")

    def generate_mermaid_diagram(self) -> str:
        """Generates a clean Mermaid architecture flowchart from the high-level components."""
        lines = ["flowchart TD"]

        # Collect subsystems (modules)
        modules = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "module"]
        api_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "api_endpoint"]
        db_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "db_model"]

        # If too small, show all files
        if len(modules) == 0:
            modules = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "file"]

        node_id_map: Dict[str, str] = {}
        idx = 1

        for m in modules[:12]:  # Limit to 12 top modules for readable diagrams
            nid = f"M{idx}"
            idx += 1
            node_id_map[m] = nid
            label = self.graph.nodes[m].get("name", m)
            lines.append(f'    {nid}["{label}"]')

        for api in api_nodes[:8]:
            nid = f"API{idx}"
            idx += 1
            node_id_map[api] = nid
            label = api.replace("api:", "")
            lines.append(f'    {nid}(["{label}"])')

        for dbm in db_nodes[:8]:
            nid = f"DB{idx}"
            idx += 1
            node_id_map[dbm] = nid
            label = self.graph.nodes[dbm].get("name", dbm)
            lines.append(f'    {nid}[("{label}")]')

        # Add edges between mapped components
        edge_count = 0
        for u, v, d in self.graph.edges(data=True):
            if u in node_id_map and v in node_id_map and u != v:
                rel = d.get("relation_type", "relates")
                lines.append(f'    {node_id_map[u]} -->|"{rel}"| {node_id_map[v]}')
                edge_count += 1
                if edge_count >= 25:
                    break

        if len(lines) == 1:
            lines.append('    EmptyRepo["Repository empty or contains no recognized modules"]')

        return "\n".join(lines)

    def persist(self, db: Session) -> Tuple[int, int]:
        """Saves all nodes and edges to PostgreSQL with atomic transaction handling."""
        # Clean existing nodes and edges for this repo
        db.execute(delete(CodeGraphEdge).where(CodeGraphEdge.repository_id == self.repository_id))
        db.execute(delete(CodeGraphNode).where(CodeGraphNode.repository_id == self.repository_id))
        db.flush()

        node_id_cache: Dict[str, int] = {}
        node_objs = []

        for key, data in self.graph.nodes(data=True):
            node = CodeGraphNode(
                repository_id=self.repository_id,
                node_key=key,
                node_type=data.get("node_type", "unknown"),
                name=data.get("name", key),
                file_path=data.get("file_path", ""),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
                metadata_json=self.node_metadata.get(key),
            )
            node_objs.append(node)

        db.add_all(node_objs)
        db.flush()

        for node in node_objs:
            node_id_cache[node.node_key] = node.id

        edge_objs = []
        for u, v, data in self.graph.edges(data=True):
            src_id = node_id_cache.get(u)
            tgt_id = node_id_cache.get(v)
            if src_id and tgt_id:
                edge = CodeGraphEdge(
                    repository_id=self.repository_id,
                    source_node_id=src_id,
                    target_node_id=tgt_id,
                    relation_type=data.get("relation_type", "relates"),
                    weight=data.get("weight", 1.0),
                    metadata_json=data.get("metadata"),
                )
                edge_objs.append(edge)

        db.add_all(edge_objs)
        db.commit()

        return len(node_objs), len(edge_objs)
