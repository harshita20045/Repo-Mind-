import math
from typing import List
from sentence_transformers import SentenceTransformer

class EmbedderError(Exception):
    pass

class LocalEmbedder:
    """
    Adapter for SentenceTransformers to generate embeddings locally.
    Validates dimensions and float validity to prevent invalid states in the DB.
    """
    EXPECTED_DIMENSIONS = 384
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        # Lazy load model in memory
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # Uses local inference, downloads model if not cached
            self._model = SentenceTransformer(self.MODEL_NAME)
        return self._model

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Embed a list of text chunks.
        Returns a list of 384-dimensional float arrays.
        """
        if not chunks:
            return []

        # Generate embeddings
        # convert_to_numpy=True returns a NumPy array which we convert to standard Python floats
        embeddings_array = self.model.encode(chunks, convert_to_numpy=True)
        
        result = []
        for emb in embeddings_array:
            float_list = emb.tolist()
            
            # Validation: 384 dimensions
            if len(float_list) != self.EXPECTED_DIMENSIONS:
                raise EmbedderError(f"Expected {self.EXPECTED_DIMENSIONS} dimensions, got {len(float_list)}")
                
            # Validation: Finite floats
            for val in float_list:
                if not isinstance(val, float):
                    raise EmbedderError("Embedding contains non-float values")
                if math.isnan(val) or math.isinf(val):
                    raise EmbedderError("Embedding contains NaN or infinite values")
                    
            result.append(float_list)
            
        return result
