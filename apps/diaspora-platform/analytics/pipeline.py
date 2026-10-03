"""
apps/diaspora-platform/analytics/pipeline.py

Complete analytics pipeline for Diaspora.

Integrates all shared_analytics components for expat community content.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field

from shared_types import ScrapedArticle
from shared_analytics import (
    SalienceScorer,
    TrustScorer,
    WeakSignalDetector,
)


@dataclass
class DiasporaAnalytics:
    """
    Complete analytics for a Diaspora article.
    
    Attributes:
        article_id: Article identifier
        salience: Salience score (0-1)
        trust: Trust score (0-1)
        importance: Combined importance
        weak_signals: Matching weak signals
        metadata: Additional analytics
    """
    article_id: str
    salience: float
    trust: float
    importance: float
    weak_signals: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'article_id': self.article_id,
            'salience': self.salience,
            'trust': self.trust,
            'importance': self.importance,
            'weak_signals': self.weak_signals,
            'metadata': self.metadata,
        }


class DiasporaAnalyticsPipeline:
    """
    Complete analytics pipeline for Diaspora community content.
    
    Integrates:
    - Salience scoring (content importance)
    - Trust scoring (source reliability)
    - Weak signal detection (emerging topics)
    
    Usage:
        pipeline = DiasporaAnalyticsPipeline(
            important_entities=['community', 'expat'],
            important_topics=['events', 'services'],
            trusted_sources=['Le Petit Journal'],
        )
        
        # Process article
        analytics = pipeline.process_article(article)
        
        print(f"Salience: {analytics.salience:.2f}")
        print(f"Trust: {analytics.trust:.2f}")
        print(f"Importance: {analytics.importance:.2f}")
    """
    
    def __init__(
        self,
        important_entities: Optional[List[str]] = None,
        important_topics: Optional[List[str]] = None,
        trusted_sources: Optional[List[str]] = None,
    ):
        """
        Initialize analytics pipeline.
        
        Args:
            important_entities: Key community entities
            important_topics: Important topics
            trusted_sources: Trusted source names
        """
        self.important_entities = important_entities or []
        self.important_topics = important_topics or []
        self.trusted_sources = trusted_sources or []
        
        # Initialize scorers
        self.salience_scorer = SalienceScorer()
        self.trust_scorer = TrustScorer()
        
        # Initialize weak signal detector
        self.weak_signal_detector = WeakSignalDetector(
            min_articles=2,
            max_articles=8,
        )
        
        # Cache for weak signals
        self._signal_cache = []
    
    def process_article(
        self,
        article: ScrapedArticle,
        engagement_data: Optional[Dict] = None,
    ) -> DiasporaAnalytics:
        """
        Process article through analytics pipeline.
        
        Args:
            article: Article to process
            engagement_data: Optional engagement metrics
            
        Returns:
            DiasporaAnalytics with complete analytics
        """
        # Calculate salience
        salience = self.salience_scorer.score(
            article,
            important_entities=self.important_entities,
            important_topics=self.important_topics,
            trusted_sources=self.trusted_sources,
            engagement_data=engagement_data or {},
        )
        
        # Calculate trust
        trust = self.trust_scorer.score_source(
            source_name=article.source_name,
        )
        
        # Combined importance
        importance = salience * trust
        
        # Find matching weak signals
        matching_signals = self._find_matching_signals(article)
        
        return DiasporaAnalytics(
            article_id=article.article_id,
            salience=salience,
            trust=trust,
            importance=importance,
            weak_signals=matching_signals,
            metadata={
                'source': article.source_name,
                'title': article.title,
            },
        )
    
    def process_batch(
        self,
        articles: List[ScrapedArticle],
    ) -> List[DiasporaAnalytics]:
        """
        Process multiple articles.
        
        Args:
            articles: Articles to process
            
        Returns:
            List of DiasporaAnalytics
        """
        return [self.process_article(article) for article in articles]
    
    def detect_weak_signals(
        self,
        articles: List[ScrapedArticle],
        baseline_keywords: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Detect weak signals in article collection.
        
        Args:
            articles: Articles to analyze
            baseline_keywords: Mainstream keywords
            
        Returns:
            List of weak signal dicts
        """
        signals = self.weak_signal_detector.detect_signals(
            articles,
            baseline_keywords=baseline_keywords,
        )
        
        # Update cache
        self._signal_cache = signals
        
        return [s.to_dict() for s in signals]
    
    def get_top_articles(
        self,
        analytics: List[DiasporaAnalytics],
        top_k: int = 10,
        sort_by: str = 'importance',
    ) -> List[DiasporaAnalytics]:
        """
        Get top articles by score.
        
        Args:
            analytics: List of analytics
            top_k: Number to return
            sort_by: 'importance', 'salience', or 'trust'
            
        Returns:
            Top K articles
        """
        if sort_by == 'importance':
            key = lambda a: a.importance
        elif sort_by == 'salience':
            key = lambda a: a.salience
        elif sort_by == 'trust':
            key = lambda a: a.trust
        else:
            raise ValueError(f"Invalid sort_by: {sort_by}")
        
        sorted_analytics = sorted(analytics, key=key, reverse=True)
        
        return sorted_analytics[:top_k]
    
    def _find_matching_signals(self, article: ScrapedArticle) -> List[str]:
        """Find weak signals matching article."""
        matching = []
        
        if not article.title:
            return matching
        
        title_lower = article.title.lower()
        
        for signal in self._signal_cache:
            # Check if signal keywords appear
            for keyword in signal.keywords[:2]:
                if keyword.lower() in title_lower:
                    matching.append(signal.signal_id)
                    break
        
        return matching


# Export
__all__ = [
    'DiasporaAnalytics',
    'DiasporaAnalyticsPipeline',
]
