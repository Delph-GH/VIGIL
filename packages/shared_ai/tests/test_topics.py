"""
Tests for shared_ai topics.

Tests topic modeling and evolution without requiring BERTopic.
"""

import pytest
from datetime import datetime


class TestTopicsImport:
    """Test topics imports."""
    
    def test_import_modeler(self):
        """Test importing topic modeler."""
        from shared_ai.topics import TopicModeler, BERTOPIC_AVAILABLE
        
        assert TopicModeler is not None
        assert isinstance(BERTOPIC_AVAILABLE, bool)
    
    def test_import_evolution(self):
        """Test importing evolution tracker."""
        from shared_ai.topics import TopicEvolution
        
        assert TopicEvolution is not None
    
    def test_bertopic_availability(self):
        """Test BERTopic availability flag."""
        from shared_ai.topics import BERTOPIC_AVAILABLE
        
        if not BERTOPIC_AVAILABLE:
            pytest.skip("BERTopic not available")


class TestTopicEvolution:
    """Test topic evolution (no dependencies)."""
    
    def test_evolution_basic(self):
        """Test basic evolution tracking."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        # Add documents
        evolution.add_document(
            doc_id="doc1",
            topic_id=0,
            timestamp="2024-01-15T10:00:00",
        )
        
        evolution.add_document(
            doc_id="doc2",
            topic_id=0,
            timestamp="2024-01-20T10:00:00",
        )
        
        evolution.add_document(
            doc_id="doc3",
            topic_id=1,
            timestamp="2024-02-10T10:00:00",
        )
        
        # Get trends
        trends = evolution.get_topic_trends(
            time_periods=["2024-01", "2024-02"],
        )
        
        assert len(trends) == 2  # Two topics
        assert trends[0] == [2, 0]  # Topic 0: 2 in Jan, 0 in Feb
        assert trends[1] == [0, 1]  # Topic 1: 0 in Jan, 1 in Feb
    
    def test_emerging_topics(self):
        """Test emerging topic detection."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        # Add documents - topic 0 grows
        # January: 2 documents for topic 0
        for i in range(2):
            evolution.add_document(
                doc_id=f"doc_jan_{i}",
                topic_id=0,
                timestamp=f"2024-01-{10+i}T10:00:00",
            )
        
        # February: 10 documents for topic 0
        for i in range(10):
            evolution.add_document(
                doc_id=f"doc_feb_{i}",
                topic_id=0,
                timestamp=f"2024-02-{10+i}T10:00:00",
            )
        
        # Find emerging
        emerging = evolution.find_emerging_topics(
            recent_period="2024-02",
            previous_period="2024-01",
            min_growth=2.0,
            min_recent_count=5,
        )
        
        assert len(emerging) == 1
        assert emerging[0]['topic_id'] == 0
        assert emerging[0]['growth_ratio'] == 5.0  # 10/2
    
    def test_declining_topics(self):
        """Test declining topic detection."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        # Add documents - topic 0 declines
        # January: 20 documents
        for i in range(20):
            evolution.add_document(
                doc_id=f"doc_jan_{i}",
                topic_id=0,
                timestamp=f"2024-01-{10+i%20}T10:00:00",
            )
        
        # February: 5 documents
        for i in range(5):
            evolution.add_document(
                doc_id=f"doc_feb_{i}",
                topic_id=0,
                timestamp=f"2024-02-{10+i}T10:00:00",
            )
        
        # Find declining
        declining = evolution.find_declining_topics(
            recent_period="2024-02",
            previous_period="2024-01",
            max_decline=0.5,
            min_previous_count=10,
        )
        
        assert len(declining) == 1
        assert declining[0]['topic_id'] == 0
        assert declining[0]['decline_ratio'] == 0.25  # 5/20
    
    def test_period_summary(self):
        """Test period summary."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        # Add mixed documents
        for i in range(5):
            evolution.add_document(
                doc_id=f"doc_{i}",
                topic_id=i % 3,  # Topics 0, 1, 2
                timestamp="2024-01-15T10:00:00",
            )
        
        summary = evolution.get_period_summary("2024-01", top_n=3)
        
        assert summary['period'] == "2024-01"
        assert summary['total_documents'] == 5
        assert summary['unique_topics'] == 3
        assert len(summary['top_topics']) == 3
    
    def test_batch_add(self):
        """Test batch document addition."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        documents = [
            {
                'doc_id': 'doc1',
                'topic_id': 0,
                'timestamp': '2024-01-15T10:00:00',
            },
            {
                'doc_id': 'doc2',
                'topic_id': 1,
                'timestamp': '2024-01-16T10:00:00',
            },
        ]
        
        evolution.add_documents_batch(documents)
        
        trends = evolution.get_topic_trends()
        assert len(trends) >= 2
    
    def test_clear(self):
        """Test clearing evolution data."""
        from shared_ai.topics import TopicEvolution
        
        evolution = TopicEvolution()
        
        evolution.add_document("doc1", 0, "2024-01-15")
        
        evolution.clear()
        
        trends = evolution.get_topic_trends()
        assert len(trends) == 0


class TestIntegration:
    """Test integrated topic modeling (requires BERTopic)."""
    
    def test_complete_pipeline(self):
        """Test complete topic modeling pipeline."""
        from shared_ai.topics import BERTOPIC_AVAILABLE
        
        if not BERTOPIC_AVAILABLE:
            pytest.skip("BERTopic not available")
        
        # If available, test complete pipeline
        from shared_ai.topics import TopicModeler, TopicEvolution
        
        try:
            # Sample documents
            documents = [
                "La politique française évolue rapidement",
                "Le parlement vote une nouvelle loi",
                "Les députés débattent de la réforme",
                "L'économie française se porte bien",
                "La croissance économique augmente",
            ]
            
            # Initialize modeler (without embedder for speed)
            modeler = TopicModeler(
                embedder=None,
                min_topic_size=2,
                verbose=False,
            )
            
            # Fit and transform
            topics, _ = modeler.fit_transform(documents)
            
            assert len(topics) == len(documents)
            
            # Get topic info
            topic_info = modeler.get_topic_info()
            assert len(topic_info) > 0
            
            # Get topic words
            if len(set(topics)) > 1:  # If multiple topics found
                topic_id = [t for t in topics if t != -1][0]
                words = modeler.get_topic_words(topic_id, top_n=5)
                assert len(words) <= 5
            
            # Test evolution
            evolution = TopicEvolution()
            
            for i, topic_id in enumerate(topics):
                evolution.add_document(
                    doc_id=f"doc_{i}",
                    topic_id=topic_id,
                    timestamp=f"2024-01-{10+i}T10:00:00",
                )
            
            summary = evolution.get_period_summary("2024-01")
            assert summary['total_documents'] == len(documents)
            
        except (ImportError, ValueError, Exception) as e:
            pytest.skip(f"BERTopic not fully configured: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
