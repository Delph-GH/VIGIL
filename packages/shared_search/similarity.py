"""
shared_search/similarity.py

High-level similarity search using FAISS and embeddings.

Integrates FAISS index with text embeddings for semantic search.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np

from .faiss_index import FAISSIndex, FAISS_AVAILABLE


class SimilaritySearch:
    """
    Semantic similarity search combining embeddings and FAISS.
    
    Features:
    - Build index from documents
    - Semantic search
    - Batch search
    - Index persistence
    
    Usage:
        from shared_ai.embeddings import TextEmbedder
        
        # Initialize
        embedder = TextEmbedder()
        search = SimilaritySearch(embedder, dimension=768)
        
        # Build index
        search.build_index(documents, doc_ids)
        
        # Search
        results = search.search("query text", top_k=5)
        
        # Save/load
        search.save("search_index")
        search = SimilaritySearch.load("search_index", embedder)
    """
    
    def __init__(
        self,
        embedder,
        dimension: int,
        index_type: str = "Flat",
        use_gpu: bool = False,
    ):
        """
        Initialize similarity search.
        
        Args:
            embedder: TextEmbedder instance
            dimension: Embedding dimension
            index_type: FAISS index type
            use_gpu: Use GPU acceleration
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required for similarity search")
        
        self.embedder = embedder
        self.dimension = dimension
        
        # Create FAISS index
        self.index = FAISSIndex(
            dimension=dimension,
            index_type=index_type,
            use_gpu=use_gpu,
        )
        
        # Document storage
        self._documents = {}  # id -> document text
    
    def build_index(
        self,
        documents: List[str],
        doc_ids: Optional[List[str]] = None,
        show_progress: bool = True,
    ):
        """
        Build index from documents.
        
        Args:
            documents: List of document texts
            doc_ids: List of document IDs
            show_progress: Show progress
        """
        if doc_ids is None:
            doc_ids = [f"doc_{i}" for i in range(len(documents))]
        
        if len(documents) != len(doc_ids):
            raise ValueError("Number of documents must match number of IDs")
        
        # Embed documents
        if show_progress:
            print(f"Embedding {len(documents)} documents...")
        
        embeddings = self.embedder.embed_batch(
            documents,
            show_progress=show_progress,
        )
        
        # Add to index
        if show_progress:
            print("Building FAISS index...")
        
        self.index.add(embeddings, ids=doc_ids)
        
        # Store documents
        for doc_id, doc in zip(doc_ids, documents):
            self._documents[doc_id] = doc
        
        if show_progress:
            print(f"Index built: {self.index.size()} documents")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        return_texts: bool = True,
    ) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results
            return_texts: Include document texts in results
            
        Returns:
            List of result dicts with id, distance, text (optional)
        """
        # Embed query
        query_embedding = self.embedder.embed(query)
        
        # Search index
        raw_results = self.index.search(query_embedding, top_k=top_k)
        
        # Format results
        results = []
        for doc_id, distance in raw_results:
            result = {
                'id': doc_id,
                'distance': distance,
                'score': 1.0 / (1.0 + distance),  # Convert distance to score
            }
            
            if return_texts and doc_id in self._documents:
                result['text'] = self._documents[doc_id]
            
            results.append(result)
        
        return results
    
    def search_batch(
        self,
        queries: List[str],
        top_k: int = 5,
        return_texts: bool = True,
    ) -> List[List[Dict]]:
        """
        Search for multiple queries.
        
        Args:
            queries: List of query texts
            top_k: Number of results per query
            return_texts: Include document texts
            
        Returns:
            List of result lists
        """
        # Embed queries
        query_embeddings = self.embedder.embed_batch(
            queries,
            show_progress=False,
        )
        
        # Search index
        raw_results = self.index.search_batch(query_embeddings, top_k=top_k)
        
        # Format results
        all_results = []
        
        for query_results in raw_results:
            results = []
            for doc_id, distance in query_results:
                result = {
                    'id': doc_id,
                    'distance': distance,
                    'score': 1.0 / (1.0 + distance),
                }
                
                if return_texts and doc_id in self._documents:
                    result['text'] = self._documents[doc_id]
                
                results.append(result)
            
            all_results.append(results)
        
        return all_results
    
    def add_documents(
        self,
        documents: List[str],
        doc_ids: Optional[List[str]] = None,
    ):
        """
        Add documents to existing index.
        
        Args:
            documents: List of document texts
            doc_ids: List of document IDs
        """
        if doc_ids is None:
            current_size = self.index.size()
            doc_ids = [f"doc_{current_size + i}" for i in range(len(documents))]
        
        # Embed and add
        embeddings = self.embedder.embed_batch(
            documents,
            show_progress=False,
        )
        
        self.index.add(embeddings, ids=doc_ids)
        
        # Store documents
        for doc_id, doc in zip(doc_ids, documents):
            self._documents[doc_id] = doc
    
    def get_document(self, doc_id: str) -> Optional[str]:
        """Get document by ID."""
        return self._documents.get(doc_id)
    
    def save(self, path: str):
        """
        Save search index.
        
        Args:
            path: Base path (will create .faiss and .docs files)
        """
        from pathlib import Path
        import json
        
        path = Path(path)
        
        # Save FAISS index
        self.index.save(f"{path}.faiss")
        
        # Save documents
        docs_path = f"{path}.docs.json"
        with open(docs_path, 'w') as f:
            json.dump(self._documents, f)
    
    @classmethod
    def load(
        cls,
        path: str,
        embedder,
        use_gpu: bool = False,
    ) -> 'SimilaritySearch':
        """
        Load search index.
        
        Args:
            path: Base path
            embedder: TextEmbedder instance
            use_gpu: Use GPU acceleration
            
        Returns:
            SimilaritySearch instance
        """
        from pathlib import Path
        import json
        
        path = Path(path)
        
        # Load FAISS index
        faiss_index = FAISSIndex.load(f"{path}.faiss", use_gpu=use_gpu)
        
        # Create instance
        instance = cls(
            embedder=embedder,
            dimension=faiss_index.dimension,
            index_type=faiss_index.index_type,
            use_gpu=use_gpu,
        )
        
        # Replace index
        instance.index = faiss_index
        
        # Load documents
        docs_path = f"{path}.docs.json"
        with open(docs_path, 'r') as f:
            instance._documents = json.load(f)
        
        return instance
    
    def size(self) -> int:
        """Get number of indexed documents."""
        return self.index.size()


# Export
__all__ = [
    'SimilaritySearch',
]
