from typing import List, Dict, Any, Optional
from backend.app.rag.chunker import TextChunker
from backend.app.intelligence.parser import ParsedCodeFile, CodeSymbol


class ASTChunk:
    def __init__(
        self,
        text: str,
        chunk_type: str,
        file_path: str,
        symbol_name: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ):
        self.text = text
        self.chunk_type = chunk_type
        self.file_path = file_path
        self.symbol_name = symbol_name
        self.start_line = start_line
        self.end_line = end_line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "chunk_type": self.chunk_type,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


class ASTCodeChunker:
    """
    Module 5: Syntax-Aware Code & Doc Chunker
    Chunks source code at logical AST boundaries (functions, classes, methods)
    and markdown documentation along structural headers rather than arbitrary line cuts.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.text_chunker = TextChunker(model_name=model_name)
        self.max_tokens = self.text_chunker.max_tokens
        self.overlap_tokens = self.text_chunker.overlap_tokens

    def chunk_parsed_code(
        self,
        file_path: str,
        content: str,
        parsed_file: Optional[ParsedCodeFile] = None,
    ) -> List[ASTChunk]:
        """Chunks source code respecting function and class boundaries."""
        if not content.strip():
            return []

        chunks: List[ASTChunk] = []
        lines = content.splitlines()

        # If no symbols or parsing failed, fallback to token-aware text chunking
        if not parsed_file or not parsed_file.symbols:
            text_slices = self.text_chunker.chunk_text(content)
            for s in text_slices:
                chunks.append(ASTChunk(
                    text=f"// File: {file_path}\n{s}",
                    chunk_type="source_code",
                    file_path=file_path,
                ))
            return chunks

        # Chunk each top-level symbol
        covered_lines = set()
        for sym in parsed_file.symbols:
            if sym.start_line and sym.end_line:
                start = max(1, sym.start_line)
                end = min(len(lines), sym.end_line)
                symbol_code = "\n".join(lines[start - 1:end])
                for line_no in range(start, end + 1):
                    covered_lines.add(line_no)

                header = f"// File: {file_path} | {sym.symbol_type}: {sym.name}\n"
                full_symbol_text = f"{header}{symbol_code}"

                # Token count check
                tokens = self.text_chunker.tokenizer.encode(full_symbol_text, add_special_tokens=False)
                if len(tokens) <= self.max_tokens:
                    chunks.append(ASTChunk(
                        text=full_symbol_text,
                        chunk_type=sym.symbol_type,
                        file_path=file_path,
                        symbol_name=sym.name,
                        start_line=start,
                        end_line=end,
                    ))
                else:
                    # Split large symbols with token chunker preserving header
                    sub_chunks = self.text_chunker.chunk_text(symbol_code)
                    for sc in sub_chunks:
                        chunks.append(ASTChunk(
                            text=f"{header}{sc}",
                            chunk_type=sym.symbol_type,
                            file_path=file_path,
                            symbol_name=sym.name,
                            start_line=start,
                            end_line=end,
                        ))

        # Check for un-chunked top-level code (imports, configs, script code)
        uncovered_blocks = []
        current_block = []
        for line_no in range(1, len(lines) + 1):
            if line_no not in covered_lines:
                current_block.append((line_no, lines[line_no - 1]))
            else:
                if current_block:
                    uncovered_blocks.append(current_block)
                    current_block = []
        if current_block:
            uncovered_blocks.append(current_block)

        for block in uncovered_blocks:
            block_text = "\n".join(l[1] for l in block).strip()
            if block_text and len(block_text) > 30:
                header = f"// File: {file_path} (module body)\n"
                sub_chunks = self.text_chunker.chunk_text(block_text)
                for sc in sub_chunks:
                    chunks.append(ASTChunk(
                        text=f"{header}{sc}",
                        chunk_type="source_code",
                        file_path=file_path,
                        start_line=block[0][0],
                        end_line=block[-1][0],
                    ))

        return chunks

    def chunk_documentation(self, file_path: str, content: str) -> List[ASTChunk]:
        """Chunks documentation files along markdown header boundaries."""
        if not content.strip():
            return []

        chunks: List[ASTChunk] = []
        sections = []
        current_header = file_path
        current_lines = []

        for line in content.splitlines():
            if line.startswith(("# ", "## ", "### ")):
                if current_lines:
                    sections.append((current_header, "\n".join(current_lines)))
                    current_lines = []
                current_header = line.lstrip("#").strip()
            current_lines.append(line)

        if current_lines:
            sections.append((current_header, "\n".join(current_lines)))

        for header, section_text in sections:
            section_tokens = self.text_chunker.tokenizer.encode(section_text, add_special_tokens=False)
            if len(section_tokens) <= self.max_tokens:
                chunks.append(ASTChunk(
                    text=f"# Document: {file_path} | Section: {header}\n{section_text}",
                    chunk_type="documentation",
                    file_path=file_path,
                    symbol_name=header,
                ))
            else:
                sub_chunks = self.text_chunker.chunk_text(section_text)
                for sc in sub_chunks:
                    chunks.append(ASTChunk(
                        text=f"# Document: {file_path} | Section: {header}\n{sc}",
                        chunk_type="documentation",
                        file_path=file_path,
                        symbol_name=header,
                    ))

        return chunks
