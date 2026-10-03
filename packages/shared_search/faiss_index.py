"""
shared_search/faiss_index.py

FAISS-based vector similarity index.

Extracted from Vigil's processing/embeddings/similarity_index.py

Features:
- FAISS index creation and management
- Vector indexing
- Index persistence (save/load)
- Top-K similarity search
"""

import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path
import json

# Optional dependency
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None


class FAISSIndex:
    """
    FAISS-based similarity index for vector search.
    
    Supports:
    - Flat (exact) search
    - IVF (inverted file) for large datasets
    - Index persistence
    - Batch operations
    
    Usage:
        # Create index
        index = FAISSIndex(dimension=768, use_gpu=False)
        
        # Add vectors
        index.add(vectors, ids=article_ids)
        
        # Search
        results = index.search(query_vector, top_k=5)
        
        # Save/load
        index.save("index.faiss")
        index = FAISSIndex.load("index.faiss")
    """
    
    def __init__(
        self,
        dimension: int,
        index_type: str = "Flat",
        use_gpu: bool = False,
    ):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Vector dimension
            index_type: Index type ("Flat", "IVF100", "IVF1000", etc.)
            use_gpu: Use GPU acceleration (requires faiss-gpu)
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS is required. Install with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_type = index_type
        self.use_gpu = use_gpu
        
        # Create index
        self.index = self._create_index()
        
        # Metadata storage (id mapping)
        self._id_to_idx = {}  # External ID -> internal index
        self._idx_to_id = {}  # Internal index -> external ID
        self._next_idx = 0
    
    def _create_index(self):
        """Create FAISS index."""
        if self.index_type == "Flat":
            # Flat index (exact search)
            index = faiss.IndexFlatL2(self.dimension)
        
        elif self.index_type.startswith("IVF"):
            # IVF index (approximate search)
            nlist = int(self.index_type.replace("IVF", ""))
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        # GPU support
        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(res, 0, index)
            except Exception as e:
                print(f"GPU acceleration failed: {e}, using CPU")
        
        return index
    
    def add(
        self,
        vectors: np.ndarray,
        ids: Optional[List[str]] = None,
    ):
        """
        Add vectors to index.
        
        Args:
            vectors: Array of vectors (n_vectors, dimension)
            ids: Optional list of IDs (if None, uses sequential IDs)
        """
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        
        n_vectors = len(vectors)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(self._next_idx + i) for i in range(n_vectors)]
        
        if len(ids) != n_vectors:
            raise ValueError(f"Number of IDs ({len(ids)}) != number of vectors ({n_vectors})")
        
        # Train index if needed (IVF requires training)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            self.index.train(vectors.astype('float32'))
        
        # Add to index
        self.index.add(vectors.astype('float32'))
        
        # Update ID mapping
        for i, external_id in enumerate(ids):
            internal_idx = self._next_idx + i
            self._id_to_idx[external_id] = internal_idx
            self._idx_to_id[internal_idx] = external_id
        
        self._next_idx += n_vectors
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            top_k: Number of results
            
        Returns:
            List of (id, distance) tuples
        """
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(
            query_vector.astype('float32'),
            top_k,
        )
        
        # Convert to results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # No result
                continue
            
            external_id = self._idx_to_id.get(idx, str(idx))
            results.append((external_id, float(distance)))
        
        return results
    
    def search_batch(
        self,
        query_vectors: np.ndarray,
        top_k: int = 5,
    ) -> List[List[Tuple[str, float]]]:
        """
        Search for multiple queries.
        
        Args:
            query_vectors: Array of query vectors (n_queries, dimension)
            top_k: Number of results per query
            
        Returns:
            List of result lists
        """
        if query_vectors.ndim == 1:
            query_vectors = query_vectors.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(
            query_vectors.astype('float32'),
            top_k,
        )
        
        # Convert to results
        all_results = []
        
        for query_indices, query_distances in zip(indices, distances):
            results = []
            for idx, distance in zip(query_indices, query_distances):
                if idx == -1:
                    continue
                
                external_id = self._idx_to_id.get(idx, str(idx))
                results.append((external_id, float(distance)))
            
            all_results.append(results)
        
        return all_results
    
    def save(self, path: str):
        """
        Save index to disk.
        
        Args:
            path: Path to save index
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        if self.use_gpu:
            # Move to CPU for saving
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, str(path))
        else:
            faiss.write_index(self.index, str(path))
        
        # Save metadata
        metadata = {
            'dimension': self.dimension,
            'index_type': self.index_type,
            'id_to_idx': self._id_to_idx,
            'idx_to_id': {str(k): v for k, v in self._idx_to_id.items()},
            'next_idx': self._next_idx,
        }
        
        metadata_path = path.with_suffix('.meta.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
    
    @classmethod
    def load(cls, path: str, use_gpu: bool = False) -> 'FAISSIndex':
        """
        Load index from disk.
        
        Args:
            path: Path to index file
            use_gpu: Use GPU acceleration
            
        Returns:
            FAISSIndex instance
        """
        path = Path(path)
        
        # Load metadata
        metadata_path = path.with_suffix('.meta.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create instance
        instance = cls(
            dimension=metadata['dimension'],
            index_type=metadata['index_type'],
            use_gpu=use_gpu,
        )
        
        # Load FAISS index
        cpu_index = faiss.read_index(str(path))
        
        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                instance.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            except Exception:
                instance.index = cpu_index
                instance.use_gpu = False
        else:
            instance.index = cpu_index
        
        # Restore metadata
        instance._id_to_idx = metadata['id_to_idx']
        instance._idx_to_id = {int(k): v for k, v in metadata['idx_to_id'].items()}
        instance._next_idx = metadata['next_idx']
        
        return instance
    
    def size(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal
    
    def reset(self):
        """Clear index."""
        self.index.reset()
        self._id_to_idx.clear()
        self._idx_to_id.clear()
        self._next_idx = 0


# Export
__all__ = [
    'FAISSIndex',
    'FAISS_AVAILABLE',
]
