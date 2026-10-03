"""
shared_ai/embeddings/embedder.py

Text embeddings using sentence-transformers and CamemBERT.

Extracted from Vigil's processing/embeddings/embedder.py

Converts French text to dense vector representations for:
- Semantic search
- Similarity comparison
- Document clustering
"""

import numpy as np
from typing import List, Optional, Union
from pathlib import Path

# Optional dependency
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class TextEmbedder:
    """
    Text to vector embeddings using sentence-transformers.
    
    Recommended models for French:
    - sentence-camembert-large (best quality, slower)
    - sentence-camembert-base (good balance)
    - paraphrase-multilingual-MiniLM-L12-v2 (fast, multilingual)
    
    Usage:
        embedder = TextEmbedder(model_name="sentence-camembert-large")
        
        # Single text
        vector = embedder.embed("Ceci est un texte français.")
        
        # Batch
        vectors = embedder.embed_batch([
            "Premier texte",
            "Deuxième texte",
            "Troisième texte",
        ])
        
        # Similarity
        similarity = embedder.cosine_similarity(vector1, vector2)
    """
    
    def __init__(
        self,
        model_name: str = "sentence-camembert-base",
        device: Optional[str] = None,
        cache_folder: Optional[str] = None,
    ):
        """
        Initialize embedder.
        
        Args:
            model_name: Sentence-transformers model name
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto)
            cache_folder: Model cache directory
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.device = device
        
        # Load model
        try:
            self.model = SentenceTransformer(
                model_name,
                device=device,
                cache_folder=cache_folder,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to load model '{model_name}': {e}\n"
                f"Available French models:\n"
                f"  - sentence-camembert-large (best)\n"
                f"  - sentence-camembert-base (recommended)\n"
                f"  - paraphrase-multilingual-MiniLM-L12-v2 (fast)"
            )
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def embed(self, text: str) -> np.ndarray:
        """
        Embed single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (numpy array)
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim)
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        
        return embedding
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Embed batch of texts efficiently.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings (shape: [n_texts, embedding_dim])
        """
        if not texts:
            return np.array([])
        
        # Filter out empty texts but track indices
        valid_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
        
        if not valid_texts:
            # All texts empty
            return np.zeros((len(texts), self.embedding_dim))
        
        # Embed valid texts
        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )
        
        # Fill in zero vectors for empty texts
        if len(valid_texts) < len(texts):
            full_embeddings = np.zeros((len(texts), self.embedding_dim))
            full_embeddings[valid_indices] = embeddings
            return full_embeddings
        
        return embeddings
    
    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Compute cosine similarity between embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0 to 1)
        """
        # Normalize
        embedding1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        embedding2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
        
        # Dot product
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, similarity)))
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: Array of candidate embeddings
            top_k: Number of results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        if len(candidate_embeddings) == 0:
            return []
        
        # Compute similarities
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return similarities[:top_k]
    
    def semantic_search(
        self,
        query: str,
        corpus_texts: List[str],
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Semantic search over corpus.
        
        Args:
            query: Query text
            corpus_texts: List of corpus texts
            top_k: Number of results
            
        Returns:
            List of (index, text, similarity_score) tuples
        """
        if not corpus_texts:
            return []
        
        # Embed query
        query_embedding = self.embed(query)
        
        # Embed corpus
        corpus_embeddings = self.embed_batch(
            corpus_texts,
            show_progress=False,
        )
        
        # Find similar
        results = self.find_most_similar(
            query_embedding,
            corpus_embeddings,
            top_k=top_k,
        )
        
        # Add texts to results
        return [
            (idx, corpus_texts[idx], score)
            for idx, score in results
        ]
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'device': str(self.model.device),
            'max_seq_length': self.model.max_seq_length,
        }


# Export
__all__ = [
    'TextEmbedder',
    'SENTENCE_TRANSFORMERS_AVAILABLE',
]
