"""
apps/vigil-platform/ai/topic_manager.py

Topic modeling and evolution tracking for Vigil.

Uses shared_ai.topics components.
"""

from typing import List, Dict, Optional
from datetime import datetime

from shared_types import ScrapedArticle
from shared_ai.embeddings import TextEmbedder
from shared_ai.topics import (
    TopicModeler,
    TopicEvolution,
    BERTOPIC_AVAILABLE,
)


class VigilTopicManager:
    """
    Manage topics for Vigil political content.
    
    Features:
    - Topic discovery on article corpus
    - Topic assignment to new articles
    - Topic evolution tracking over time
    - Emerging topic detection
    
    Usage:
        # Initialize with embedder
        from shared_ai.embeddings import TextEmbedder
        
        embedder = TextEmbedder(model_name="sentence-camembert-base")
        
        manager = VigilTopicManager(
            embedder=embedder,
            min_topic_size=10,
        )
        
        # Fit on corpus
        manager.fit_corpus(articles)
        
        # Assign topics to new articles
        topics = manager.assign_topics(new_articles)
        
        # Track evolution
        manager.track_evolution(articles)
        
        # Find emerging topics
        emerging = manager.get_emerging_topics(
            recent_period="2024-03",
            previous_period="2024-02",
        )
    """
    
    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        min_topic_size: int = 10,
        enable_evolution: bool = True,
    ):
        """
        Initialize topic manager.
        
        Args:
            embedder: TextEmbedder instance
            min_topic_size: Minimum topic size
            enable_evolution: Enable evolution tracking
        """
        if not BERTOPIC_AVAILABLE:
            raise ImportError(
                "BERTopic is required for topic modeling. "
                "Install with: pip install bertopic umap-learn hdbscan"
            )
        
        self.embedder = embedder
        self.min_topic_size = min_topic_size
        
        # Initialize topic modeler
        self.modeler = TopicModeler(
            embedder=embedder,
            language="french",
            min_topic_size=min_topic_size,
            verbose=False,
        )
        
        # Initialize evolution tracker
        if enable_evolution:
            self.evolution = TopicEvolution()
        else:
            self.evolution = None
        
        # Track if fitted
        self._fitted = False
    
    def fit_corpus(self, articles: List[ScrapedArticle]) -> Dict:
        """
        Fit topic model on article corpus.
        
        Args:
            articles: List of articles
            
        Returns:
            Summary dictionary
        """
        # Extract texts
        texts = [self._get_text(article) for article in articles]
        
        # Fit model
        topics, _ = self.modeler.fit_transform(texts)
        
        self._fitted = True
        
        # Get topic info
        topic_info = self.modeler.get_topic_info()
        
        return {
            'num_articles': len(articles),
            'num_topics': len(topic_info),
            'topics': topic_info,
        }
    
    def assign_topics(
        self,
        articles: List[ScrapedArticle],
    ) -> List[Dict]:
        """
        Assign topics to articles.
        
        Args:
            articles: List of articles
            
        Returns:
            List of dicts with topic assignments
        """
        if not self._fitted:
            raise ValueError("Model must be fitted first. Call fit_corpus()")
        
        # Extract texts
        texts = [self._get_text(article) for article in articles]
        
        # Transform
        topics, probs = self.modeler.transform(texts)
        
        # Build results
        results = []
        
        for article, topic_id, prob in zip(articles, topics, probs):
            # Get topic words
            topic_words = self.modeler.get_topic_words(topic_id, top_n=5)
            
            results.append({
                'article_id': article.article_id,
                'topic': topic_id,
                'probability': float(prob[topic_id]) if len(prob) > 0 else 0.0,
                'topic_words': topic_words,
            })
        
        return results
    
    def track_evolution(
        self,
        articles: List[ScrapedArticle],
        topics: Optional[List[int]] = None,
    ):
        """
        Add articles to evolution tracker.
        
        Args:
            articles: List of articles
            topics: List of topic IDs (if None, will assign)
        """
        if not self.evolution:
            raise ValueError("Evolution tracking not enabled")
        
        # Assign topics if needed
        if topics is None:
            if not self._fitted:
                raise ValueError("Model must be fitted first")
            
            texts = [self._get_text(article) for article in articles]
            topics, _ = self.modeler.transform(texts)
        
        # Add to evolution tracker
        for article, topic_id in zip(articles, topics):
            # Get timestamp
            timestamp = article.scraped_at or datetime.now().isoformat()
            
            self.evolution.add_document(
                doc_id=article.article_id,
                topic_id=topic_id,
                timestamp=timestamp,
            )
    
    def get_topic_trends(
        self,
        time_periods: Optional[List[str]] = None,
    ) -> Dict[int, List[int]]:
        """
        Get topic trends over time.
        
        Args:
            time_periods: List of time periods
            
        Returns:
            Dictionary of topic trends
        """
        if not self.evolution:
            raise ValueError("Evolution tracking not enabled")
        
        return self.evolution.get_topic_trends(time_periods)
    
    def get_emerging_topics(
        self,
        recent_period: str,
        previous_period: str,
        min_growth: float = 2.0,
    ) -> List[Dict]:
        """
        Find emerging topics.
        
        Args:
            recent_period: Recent time period
            previous_period: Previous time period
            min_growth: Minimum growth ratio
            
        Returns:
            List of emerging topics with info
        """
        if not self.evolution:
            raise ValueError("Evolution tracking not enabled")
        
        emerging = self.evolution.find_emerging_topics(
            recent_period=recent_period,
            previous_period=previous_period,
            min_growth=min_growth,
        )
        
        # Add topic words
        for topic in emerging:
            topic_id = topic['topic_id']
            words = self.modeler.get_topic_words(topic_id, top_n=5)
            topic['topic_words'] = words
        
        return emerging
    
    def get_declining_topics(
        self,
        recent_period: str,
        previous_period: str,
        max_decline: float = 0.5,
    ) -> List[Dict]:
        """
        Find declining topics.
        
        Args:
            recent_period: Recent time period
            previous_period: Previous time period
            max_decline: Maximum decline ratio
            
        Returns:
            List of declining topics with info
        """
        if not self.evolution:
            raise ValueError("Evolution tracking not enabled")
        
        declining = self.evolution.find_declining_topics(
            recent_period=recent_period,
            previous_period=previous_period,
            max_decline=max_decline,
        )
        
        # Add topic words
        for topic in declining:
            topic_id = topic['topic_id']
            words = self.modeler.get_topic_words(topic_id, top_n=5)
            topic['topic_words'] = words
        
        return declining
    
    def _get_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
        if article.body_text:
            return article.body_text
        elif article.title:
            return article.title
        else:
            return ""


# Export
__all__ = [
    'VigilTopicManager',
]
