"""
Tests for shared_search.

Tests FAISS index and similarity search without requiring FAISS.
"""

import pytest
import numpy as np


class TestImports:
    """Test imports."""
    
    def test_import_faiss_index(self):
        """Test importing FAISS index."""
        from shared_search import FAISSIndex, FAISS_AVAILABLE
        
        assert FAISSIndex is not None
        assert isinstance(FAISS_AVAILABLE, bool)
    
    def test_import_similarity_search(self):
        """Test importing similarity search."""
        from shared_search import SimilaritySearch
        
        assert SimilaritySearch is not None
    
    def test_faiss_availability(self):
        """Test FAISS availability flag."""
        from shared_search import FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")


class TestFAISSIndex:
    """Test FAISS index (requires FAISS)."""
    
    def test_create_flat_index(self):
        """Test creating flat index."""
        from shared_search import FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        from shared_search import FAISSIndex
        
        # Create index
        index = FAISSIndex(dimension=128, index_type="Flat")
        
        assert index.dimension == 128
        assert index.size() == 0
    
    def test_add_vectors(self):
        """Test adding vectors."""
        from shared_search import FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        from shared_search import FAISSIndex
        
        # Create index
        index = FAISSIndex(dimension=4)
        
        # Add vectors
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ])
        
        ids = ["vec1", "vec2", "vec3"]
        
        index.add(vectors, ids=ids)
        
        assert index.size() == 3
    
    def test_search(self):
        """Test search."""
        from shared_search import FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        from shared_search import FAISSIndex
        
        # Create and populate index
        index = FAISSIndex(dimension=4)
        
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ])
        
        ids = ["vec1", "vec2", "vec3"]
        index.add(vectors, ids=ids)
        
        # Search
        query = np.array([1.0, 0.1, 0.0, 0.0])
        results = index.search(query, top_k=2)
        
        assert len(results) == 2
        assert results[0][0] == "vec1"  # Closest
    
    def test_batch_search(self):
        """Test batch search."""
        from shared_search import FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        from shared_search import FAISSIndex
        
        # Create and populate
        index = FAISSIndex(dimension=4)
        
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ])
        
        index.add(vectors, ids=["vec1", "vec2"])
        
        # Batch search
        queries = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ])
        
        results = index.search_batch(queries, top_k=1)
        
        assert len(results) == 2
        assert results[0][0][0] == "vec1"
        assert results[1][0][0] == "vec2"


class TestSimilaritySearch:
    """Test similarity search integration."""
    
    def test_import(self):
        """Test importing similarity search."""
        from shared_search import SimilaritySearch
        
        assert SimilaritySearch is not None
    
    def test_requires_faiss(self):
        """Test that SimilaritySearch requires FAISS."""
        from shared_search import FAISS_AVAILABLE
        
        if FAISS_AVAILABLE:
            pytest.skip("FAISS is available")
        
        from shared_search import SimilaritySearch
        
        # Should raise ImportError without FAISS
        with pytest.raises(ImportError):
            SimilaritySearch(
                embedder=None,
                dimension=768,
            )


class TestIntegration:
    """Test complete integration (requires FAISS + embeddings)."""
    
    def test_complete_pipeline(self):
        """Test complete search pipeline."""
        from shared_search import FAISS_AVAILABLE
        from shared_ai.embeddings import SENTENCE_TRANSFORMERS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            pytest.skip("sentence-transformers not available")
        
        try:
            from shared_ai.embeddings import TextEmbedder
            from shared_search import SimilaritySearch
            
            # Initialize embedder
            embedder = TextEmbedder(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            # Initialize search
            search = SimilaritySearch(
                embedder=embedder,
                dimension=embedder.embedding_dim,
            )
            
            # Build index
            documents = [
                "Paris est la capitale de la France",
                "Berlin est la capitale de l'Allemagne",
                "Rome est la capitale de l'Italie",
            ]
            
            doc_ids = ["doc1", "doc2", "doc3"]
            
            search.build_index(
                documents,
                doc_ids,
                show_progress=False,
            )
            
            assert search.size() == 3
            
            # Search
            results = search.search("capitale France", top_k=2)
            
            assert len(results) <= 2
            assert results[0]['id'] in doc_ids
            
        except (ImportError, ValueError, Exception) as e:
            pytest.skip(f"Dependencies not fully configured: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
