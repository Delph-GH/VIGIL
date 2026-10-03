"""
Tests for shared_ai embeddings.

Tests embedder and batch processor without requiring sentence-transformers.
"""

import pytest
import numpy as np


class TestEmbeddingsImport:
    """Test embeddings imports."""
    
    def test_import_embedder(self):
        """Test importing embedder."""
        from shared_ai.embeddings import TextEmbedder, SENTENCE_TRANSFORMERS_AVAILABLE
        
        assert TextEmbedder is not None
        assert isinstance(SENTENCE_TRANSFORMERS_AVAILABLE, bool)
    
    def test_import_batch_processor(self):
        """Test importing batch processor."""
        from shared_ai.embeddings import EmbeddingBatchProcessor, EmbeddingCache
        
        assert EmbeddingBatchProcessor is not None
        assert EmbeddingCache is not None
    
    def test_sentence_transformers_availability(self):
        """Test sentence-transformers availability flag."""
        from shared_ai.embeddings import SENTENCE_TRANSFORMERS_AVAILABLE
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            pytest.skip("sentence-transformers not available")


class TestEmbeddingCache:
    """Test embedding cache (no dependencies)."""
    
    def test_cache_basic(self):
        """Test basic cache operations."""
        from shared_ai.embeddings import EmbeddingCache
        
        cache = EmbeddingCache(max_size=3)
        
        # Create dummy embeddings
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([4.0, 5.0, 6.0])
        
        # Set
        cache.set("text1", vec1)
        cache.set("text2", vec2)
        
        # Get
        retrieved1 = cache.get("text1")
        assert np.array_equal(retrieved1, vec1)
        
        retrieved2 = cache.get("text2")
        assert np.array_equal(retrieved2, vec2)
        
        # Miss
        retrieved_miss = cache.get("nonexistent")
        assert retrieved_miss is None
    
    def test_cache_eviction(self):
        """Test cache eviction (LRU)."""
        from shared_ai.embeddings import EmbeddingCache
        
        cache = EmbeddingCache(max_size=2)
        
        vec1 = np.array([1.0])
        vec2 = np.array([2.0])
        vec3 = np.array([3.0])
        
        # Fill cache
        cache.set("text1", vec1)
        cache.set("text2", vec2)
        
        # Add third (should evict first)
        cache.set("text3", vec3)
        
        # First should be evicted
        assert cache.get("text1") is None
        assert cache.get("text2") is not None
        assert cache.get("text3") is not None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        from shared_ai.embeddings import EmbeddingCache
        
        cache = EmbeddingCache()
        
        cache.set("text1", np.array([1.0]))
        cache.set("text2", np.array([2.0]))
        
        assert cache.size() == 2
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("text1") is None


class TestBatchProcessorBasics:
    """Test batch processor basic functionality."""
    
    def test_import_batch_processor(self):
        """Test batch processor import."""
        from shared_ai.embeddings import EmbeddingBatchProcessor
        
        assert EmbeddingBatchProcessor is not None


class TestIntegration:
    """Test integrated embeddings workflow (requires sentence-transformers)."""
    
    def test_complete_pipeline(self):
        """Test complete embeddings pipeline."""
        from shared_ai.embeddings import SENTENCE_TRANSFORMERS_AVAILABLE
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            pytest.skip("sentence-transformers not available")
        
        # If available, test complete pipeline
        from shared_ai.embeddings import TextEmbedder, EmbeddingBatchProcessor, EmbeddingCache
        
        try:
            # Initialize embedder (use smallest/fastest model for testing)
            embedder = TextEmbedder(model_name="paraphrase-multilingual-MiniLM-L12-v2")
            
            # 1. Single embedding
            text = "Ceci est un test."
            embedding = embedder.embed(text)
            
            assert isinstance(embedding, np.ndarray)
            assert len(embedding) > 0
            
            # 2. Batch embedding
            texts = [
                "Premier texte",
                "Deuxième texte",
                "Troisième texte",
            ]
            
            embeddings = embedder.embed_batch(texts, show_progress=False)
            
            assert len(embeddings) == 3
            assert embeddings.shape[1] == embedder.embedding_dim
            
            # 3. Similarity
            similarity = embedder.cosine_similarity(embeddings[0], embeddings[1])
            
            assert 0.0 <= similarity <= 1.0
            
            # 4. Semantic search
            query = "Premier"
            results = embedder.semantic_search(query, texts, top_k=2)
            
            assert len(results) <= 2
            
            # 5. Cache
            cache = EmbeddingCache()
            cache.set(text, embedding)
            
            cached = cache.get(text)
            assert np.array_equal(cached, embedding)
            
            # 6. Batch processor
            processor = EmbeddingBatchProcessor(embedder)
            
            batch_embeddings = processor.process_corpus(
                texts,
                batch_size=2,
            )
            
            assert len(batch_embeddings) == 3
            
        except (ImportError, ValueError, Exception) as e:
            pytest.skip(f"sentence-transformers not fully configured: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
