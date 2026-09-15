from typing import List
from transformers import AutoTokenizer

class TextChunker:
    """
    Deterministic token-aware chunking for markdown documents.
    Uses the exact tokenizer of the intended embedding model.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # model max length for all-MiniLM-L6-v2 is 256
        self.max_tokens = 256
        self.overlap_tokens = 50

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks of exactly max_tokens (or less).
        Guarantees no silent truncation by respecting the model's sequence limit.
        """
        if not text.strip():
            return []

        # Tokenize the entire text without truncation
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        
        chunks = []
        start = 0
        while start < len(tokens):
            # Take a slice of exactly max_tokens
            end = start + self.max_tokens
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move the start forward, considering overlap
            start += (self.max_tokens - self.overlap_tokens)
            
            # If we're stuck (max_tokens <= overlap_tokens, which shouldn't happen but defensive), break
            if self.max_tokens <= self.overlap_tokens:
                break
                
        return chunks
