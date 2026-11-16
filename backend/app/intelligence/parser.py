import ast
import re
from typing import List, Dict, Any, Optional

try:
    import tree_sitter
    import tree_sitter_javascript
    import tree_sitter_typescript
    _HAS_TREE_SITTER = True
    _JS_LANGUAGE = tree_sitter.Language(tree_sitter_javascript.language())
    _TS_LANGUAGE = tree_sitter.Language(tree_sitter_typescript.language_typescript())
    _TSX_LANGUAGE = tree_sitter.Language(tree_sitter_typescript.language_tsx())
except Exception:
    _HAS_TREE_SITTER = False
    _JS_LANGUAGE = None
    _TS_LANGUAGE = None
    _TSX_LANGUAGE = None


class CodeSymbol:
    def __init__(
        self,
        name: str,
        symbol_type: str,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        signature: Optional[str] = None,
        docstring: Optional[str] = None,
        parent_symbol: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.symbol_type = symbol_type
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.signature = signature
        self.docstring = docstring
        self.parent_symbol = parent_symbol
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol_type": self.symbol_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "signature": self.signature,
            "docstring": self.docstring,
            "parent_symbol": self.parent_symbol,
            "metadata": self.metadata,
        }


class ParsedCodeFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbols: List[CodeSymbol] = []
        self.imports: List[Dict[str, Any]] = []
        self.exports: List[Dict[str, Any]] = []
        self.calls: List[Dict[str, Any]] = []
        self.api_definitions: List[Dict[str, Any]] = []
        self.db_interactions: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
            "exports": self.exports,
            "calls": self.calls,
            "api_definitions": self.api_definitions,
            "db_interactions": self.db_interactions,
        }


class LanguageAwareParser:
    """
    Module 2: Language-Aware Code Parser
    Extracts classes, functions, methods, imports, exports, API definitions,
    database interactions, and function calls from Python and JS/TS files.
    """

    def parse_file(self, file_path: str, content: str) -> ParsedCodeFile:
        parsed = ParsedCodeFile(file_path)
        clean_path = file_path.replace("\\", "/")
        ext = clean_path.split(".")[-1].lower() if "." in clean_path else ""

        if ext == "py":
            self._parse_python(parsed, content)
        elif ext in ("js", "jsx", "ts", "tsx", "mjs"):
            self._parse_javascript_typescript(parsed, content, ext)

        return parsed

    # -------------------------------------------------------------------------
    # Python Parser (Standard library AST)
    # -------------------------------------------------------------------------
    def _parse_python(self, parsed: ParsedCodeFile, content: str) -> None:
        try:
            tree = ast.parse(content)
        except Exception:
            return  # Skip files with syntax errors safely

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._extract_python_import(parsed, node)
            elif isinstance(node, ast.ClassDef):
                self._extract_python_class(parsed, node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_python_function(parsed, node, parent_class=None)
            elif isinstance(node, ast.Assign):
                # Check for __all__ exports
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    parsed.exports.append({"name": elt.value, "line": node.lineno})

        # Second pass for calls and DB interactions
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._extract_python_call(parsed, node)

    def _extract_python_import(self, parsed: ParsedCodeFile, node: Any) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                parsed.imports.append({
                    "module": alias.name,
                    "names": [alias.name],
                    "alias": alias.asname,
                    "line": node.lineno,
                    "is_from": False,
                })
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            parsed.imports.append({
                "module": node.module or "",
                "names": names,
                "line": node.lineno,
                "is_from": True,
            })

    def _extract_python_class(self, parsed: ParsedCodeFile, node: ast.ClassDef) -> None:
        doc = ast.get_docstring(node)
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.attr}")

        is_db_model = any(b in ("Base", "Model", "DeclarativeBase") for b in bases)
        sym_type = "db_model" if is_db_model else "class"

        parsed.symbols.append(CodeSymbol(
            name=node.name,
            symbol_type=sym_type,
            file_path=parsed.file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            docstring=doc,
            metadata={"bases": bases, "is_db_model": is_db_model},
        ))

        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_python_function(parsed, child, parent_class=node.name)

    def _extract_python_function(self, parsed: ParsedCodeFile, node: Any, parent_class: Optional[str]) -> None:
        doc = ast.get_docstring(node)
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{dec.attr}")
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(f"{dec.func.attr}")

        # Check API Route decorators (@app.get, @router.post, etc.)
        api_route = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                method_name = dec.func.attr.upper()
                if method_name in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    route_path = ""
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        route_path = str(dec.args[0].value)
                    api_route = {"method": method_name, "path": route_path, "handler": node.name, "line": node.lineno}
                    parsed.api_definitions.append(api_route)

        symbol_type = "api_endpoint" if api_route else ("method" if parent_class else "function")
        args_names = [arg.arg for arg in node.args.args]
        sig = f"def {node.name}({', '.join(args_names)})"

        parsed.symbols.append(CodeSymbol(
            name=node.name,
            symbol_type=symbol_type,
            file_path=parsed.file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            signature=sig,
            docstring=doc,
            parent_symbol=parent_class,
            metadata={"decorators": decorators, "is_async": isinstance(node, ast.AsyncFunctionDef), "api_route": api_route},
        ))

    def _extract_python_call(self, parsed: ParsedCodeFile, node: ast.Call) -> None:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # Detect DB interaction calls
            if func_name in ("query", "execute", "select", "filter", "where", "commit", "flush", "add", "delete"):
                parsed.db_interactions.append({
                    "operation": func_name,
                    "line": node.lineno,
                })

        if func_name:
            parsed.calls.append({"callee": func_name, "line": node.lineno})

    # -------------------------------------------------------------------------
    # JavaScript & TypeScript Parser
    # -------------------------------------------------------------------------
    def _parse_javascript_typescript(self, parsed: ParsedCodeFile, content: str, ext: str) -> None:
        if _HAS_TREE_SITTER:
            try:
                lang = _TSX_LANGUAGE if ext in ("tsx", "jsx") else (_TS_LANGUAGE if ext == "ts" else _JS_LANGUAGE)
                parser = tree_sitter.Parser(lang)
                tree = parser.parse(content.encode("utf-8"))
                self._traverse_tree_sitter_node(parsed, tree.root_node, content.encode("utf-8"))
                return
            except Exception:
                pass

        # Fallback lexical parser if tree-sitter is unavailable or fails
        self._fallback_js_parse(parsed, content)

    def _traverse_tree_sitter_node(self, parsed: ParsedCodeFile, node: Any, src_bytes: bytes) -> None:
        node_type = node.type

        # Class declaration
        if node_type in ("class_declaration", "class"):
            name_node = node.child_by_field_name("name")
            name = src_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "AnonymousClass"
            parsed.symbols.append(CodeSymbol(
                name=name,
                symbol_type="class",
                file_path=parsed.file_path,
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            ))

        # Function declaration
        elif node_type in ("function_declaration", "generator_function_declaration"):
            name_node = node.child_by_field_name("name")
            name = src_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "anonymous"
            parsed.symbols.append(CodeSymbol(
                name=name,
                symbol_type="function",
                file_path=parsed.file_path,
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            ))

        # Method definition
        elif node_type in ("method_definition",):
            name_node = node.child_by_field_name("name")
            name = src_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "anonymous"
            parsed.symbols.append(CodeSymbol(
                name=name,
                symbol_type="method",
                file_path=parsed.file_path,
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            ))

        # Import statement
        elif node_type in ("import_statement",):
            stmt_text = src_bytes[node.start_byte:node.end_byte].decode("utf-8")
            parsed.imports.append({"statement": stmt_text, "line": node.start_point.row + 1})

        # Export statement
        elif node_type in ("export_statement",):
            stmt_text = src_bytes[node.start_byte:node.end_byte].decode("utf-8")
            parsed.exports.append({"statement": stmt_text, "line": node.start_point.row + 1})

        # Call expression
        elif node_type in ("call_expression",):
            fn_node = node.child_by_field_name("function")
            if fn_node:
                fn_name = src_bytes[fn_node.start_byte:fn_node.end_byte].decode("utf-8")
                parsed.calls.append({"callee": fn_name, "line": node.start_point.row + 1})

        for child in node.children:
            self._traverse_tree_sitter_node(parsed, child, src_bytes)

    def _fallback_js_parse(self, parsed: ParsedCodeFile, content: str) -> None:
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            sline = line.strip()
            # Imports
            if sline.startswith("import "):
                parsed.imports.append({"statement": sline, "line": idx})
            # Exports
            elif sline.startswith("export "):
                parsed.exports.append({"statement": sline, "line": idx})
            # Classes
            m_class = re.match(r"(?:export\s+)?class\s+([A-Za-z0-9_$]+)", sline)
            if m_class:
                parsed.symbols.append(CodeSymbol(name=m_class.group(1), symbol_type="class", file_path=parsed.file_path, start_line=idx))
            # Functions
            m_func = re.match(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)", sline)
            if m_func:
                parsed.symbols.append(CodeSymbol(name=m_func.group(1), symbol_type="function", file_path=parsed.file_path, start_line=idx))
            # Arrow functions: const myFunc = (...) =>
            m_arrow = re.match(r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", sline)
            if m_arrow:
                parsed.symbols.append(CodeSymbol(name=m_arrow.group(1), symbol_type="function", file_path=parsed.file_path, start_line=idx))
