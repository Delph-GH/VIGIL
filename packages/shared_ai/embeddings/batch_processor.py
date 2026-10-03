"""
shared_ai/embeddings/batch_processor.py

Batch processing utilities for embeddings.

Extracted from Vigil's processing/embeddings/batch_processor.py

Handles:
- Large-scale batch processing
- Progress tracking
- Memory management
- Caching
"""

import numpy as np
from typing import List, Optional, Dict, Callable
from pathlib import Path
import json
from datetime import datetime


class EmbeddingBatchProcessor:
    """
    Batch processor for efficient embedding generation.
    
    Features:
    - Chunked processing for large datasets
    - Progress tracking
    - Automatic caching
    - Memory-efficient iteration
    
    Usage:
        from shared_ai.embeddings import TextEmbedder
        
        embedder = TextEmbedder()
        processor = EmbeddingBatchProcessor(embedder)
        
        # Process large corpus
        embeddings = processor.process_corpus(
            texts=large_text_list,
            batch_size=64,
            cache_file="embeddings.npy",
        )
        
        # With progress callback
        def progress(current, total):
            print(f"Progress: {current}/{total}")
        
        embeddings = processor.process_corpus(
            texts=texts,
            progress_callback=progress,
        )
    """
    
    def __init__(self, embedder):
        """
        Initialize batch processor.
        
        Args:
            embedder: TextEmbedder instance
        """
        self.embedder = embedder
    
    def process_corpus(
        self,
        texts: List[str],
        batch_size: int = 32,
        cache_file: Optional[str] = None,
        force_recompute: bool = False,
        progress_callback: Optional[Callable] = None,
    ) -> np.ndarray:
        """
        Process entire corpus with batching and caching.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size
            cache_file: Path to cache file (.npy)
            force_recompute: Force recomputation even if cached
            progress_callback: Callback(current, total)
            
        Returns:
            Array of embeddings
        """
        # Check cache
        if cache_file and not force_recompute:
            cached = self._load_cache(cache_file, len(texts))
            if cached is not None:
                return cached
        
        # Process in batches
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Embed batch
            batch_embeddings = self.embedder.embed_batch(
                batch_texts,
                batch_size=batch_size,
                show_progress=False,
            )
            
            all_embeddings.append(batch_embeddings)
            
            # Progress callback
            if progress_callback:
                current_batch = (i // batch_size) + 1
                progress_callback(current_batch, total_batches)
        
        # Concatenate
        embeddings = np.vstack(all_embeddings)
        
        # Cache
        if cache_file:
            self._save_cache(cache_file, embeddings, texts)
        
        return embeddings
    
    def process_documents(
        self,
        documents: List[Dict],
        text_field: str = 'text',
        batch_size: int = 32,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict]:
        """
        Process documents and add embeddings.
        
        Args:
            documents: List of document dicts
            text_field: Field containing text to embed
            batch_size: Batch size
            progress_callback: Progress callback
            
        Returns:
            Documents with 'embedding' field added
        """
        # Extract texts
        texts = [doc.get(text_field, "") for doc in documents]
        
        # Embed
        embeddings = self.process_corpus(
            texts,
            batch_size=batch_size,
            progress_callback=progress_callback,
        )
        
        # Add embeddings to documents
        for doc, embedding in zip(documents, embeddings):
            doc['embedding'] = embedding
            doc['embedding_model'] = self.embedder.model_name
            doc['embedding_dim'] = self.embedder.embedding_dim
        
        return documents
    
    def _load_cache(
        self,
        cache_file: str,
        expected_count: int,
    ) -> Optional[np.ndarray]:
        """
        Load embeddings from cache.
        
        Args:
            cache_file: Cache file path
            expected_count: Expected number of embeddings
            
        Returns:
            Cached embeddings or None
        """
        cache_path = Path(cache_file)
        
        if not cache_path.exists():
            return None
        
        try:
            # Load embeddings
            embeddings = np.load(cache_file)
            
            # Verify count
            if len(embeddings) != expected_count:
                return None
            
            # Load metadata
            meta_file = cache_path.with_suffix('.meta.json')
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                # Verify model
                if metadata.get('model_name') != self.embedder.model_name:
                    return None
            
            return embeddings
        
        except Exception:
            return None
    
    def _save_cache(
        self,
        cache_file: str,
        embeddings: np.ndarray,
        texts: List[str],
    ):
        """
        Save embeddings to cache.
        
        Args:
            cache_file: Cache file path
            embeddings: Embeddings array
            texts: Original texts (for metadata)
        """
        cache_path = Path(cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings
        np.save(cache_file, embeddings)
        
        # Save metadata
        meta_file = cache_path.with_suffix('.meta.json')
        metadata = {
            'model_name': self.embedder.model_name,
            'embedding_dim': self.embedder.embedding_dim,
            'count': len(embeddings),
            'created_at': datetime.now().isoformat(),
        }
        
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)


class EmbeddingCache:
    """
    Simple embedding cache for repeated queries.
    
    Usage:
        cache = EmbeddingCache(max_size=1000)
        
        # Try to get from cache
        embedding = cache.get(text)
        
        if embedding is None:
            # Compute and cache
            embedding = embedder.embed(text)
            cache.set(text, embedding)
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum cache size
        """
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}
        self.access_order: List[str] = []
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache.
        
        Args:
            text: Query text
            
        Returns:
            Cached embedding or None
        """
        if text in self.cache:
            # Update access order (move to end)
            self.access_order.remove(text)
            self.access_order.append(text)
            
            return self.cache[text]
        
        return None
    
    def set(self, text: str, embedding: np.ndarray):
        """
        Add embedding to cache.
        
        Args:
            text: Query text
            embedding: Embedding vector
        """
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and text not in self.cache:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        # Add to cache
        self.cache[text] = embedding
        
        if text not in self.access_order:
            self.access_order.append(text)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)


# Export
__all__ = [
    'EmbeddingBatchProcessor',
    'EmbeddingCache',
]
