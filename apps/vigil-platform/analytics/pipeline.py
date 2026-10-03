"""
apps/vigil-platform/analytics/pipeline.py

Complete analytics pipeline for Vigil.

Integrates all shared_analytics components for political content.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field

from shared_types import ScrapedArticle
from shared_analytics import (
    SalienceScorer,
    TrustScorer,
    NarrativeDetector,
)


@dataclass
class VigilAnalytics:
    """
    Complete analytics for a Vigil article.
    
    Attributes:
        article_id: Article identifier
        salience: Salience score (0-1)
        trust: Trust score (0-1)
        importance: Combined importance (salience × trust)
        narratives: Matching narratives
        metadata: Additional analytics
    """
    article_id: str
    salience: float
    trust: float
    importance: float
    narratives: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'article_id': self.article_id,
            'salience': self.salience,
            'trust': self.trust,
            'importance': self.importance,
            'narratives': self.narratives,
            'metadata': self.metadata,
        }


class VigilAnalyticsPipeline:
    """
    Complete analytics pipeline for Vigil political content.
    
    Integrates:
    - Salience scoring (article importance)
    - Trust scoring (source reliability)
    - Narrative detection (emergent themes)
    
    Usage:
        pipeline = VigilAnalyticsPipeline(
            important_entities=['Macron', 'Borne'],
            important_topics=['réforme', 'politique'],
            trusted_sources=['Le Monde', 'AFP'],
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
        salience_weights: Optional[Dict] = None,
        trust_weights: Optional[Dict] = None,
    ):
        """
        Initialize analytics pipeline.
        
        Args:
            important_entities: Key political entities
            important_topics: Important topics
            trusted_sources: Trusted source names
            salience_weights: Custom salience weights
            trust_weights: Custom trust weights
        """
        self.important_entities = important_entities or []
        self.important_topics = important_topics or []
        self.trusted_sources = trusted_sources or []
        
        # Initialize scorers
        if salience_weights:
            self.salience_scorer = SalienceScorer(**salience_weights)
        else:
            self.salience_scorer = SalienceScorer()
        
        if trust_weights:
            self.trust_scorer = TrustScorer(**trust_weights)
        else:
            self.trust_scorer = TrustScorer()
        
        # Initialize narrative detector
        self.narrative_detector = NarrativeDetector(min_articles=3)
        
        # Cache for narratives
        self._narrative_cache = []
    
    def process_article(
        self,
        article: ScrapedArticle,
        engagement_data: Optional[Dict] = None,
    ) -> VigilAnalytics:
        """
        Process article through analytics pipeline.
        
        Args:
            article: Article to process
            engagement_data: Optional engagement metrics
            
        Returns:
            VigilAnalytics with complete analytics
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
        
        # Find matching narratives
        matching_narratives = self._find_matching_narratives(article)
        
        return VigilAnalytics(
            article_id=article.article_id,
            salience=salience,
            trust=trust,
            importance=importance,
            narratives=matching_narratives,
            metadata={
                'source': article.source_name,
                'title': article.title,
            },
        )
    
    def process_batch(
        self,
        articles: List[ScrapedArticle],
    ) -> List[VigilAnalytics]:
        """
        Process multiple articles.
        
        Args:
            articles: Articles to process
            
        Returns:
            List of VigilAnalytics
        """
        return [self.process_article(article) for article in articles]
    
    def detect_narratives(
        self,
        articles: List[ScrapedArticle],
    ) -> List[Dict]:
        """
        Detect narratives in article collection.
        
        Args:
            articles: Articles to analyze
            
        Returns:
            List of narrative dicts
        """
        narratives = self.narrative_detector.detect_narratives(articles)
        
        # Update cache
        self._narrative_cache = narratives
        
        return [n.to_dict() for n in narratives]
    
    def get_top_articles(
        self,
        analytics: List[VigilAnalytics],
        top_k: int = 10,
        sort_by: str = 'importance',
    ) -> List[VigilAnalytics]:
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
    
    def _find_matching_narratives(self, article: ScrapedArticle) -> List[str]:
        """Find narratives matching article."""
        matching = []
        
        # Simple matching based on keywords in title
        if not article.title:
            return matching
        
        title_lower = article.title.lower()
        
        for narrative in self._narrative_cache:
            # Check if narrative keywords appear in article
            for keyword in narrative.keywords[:3]:  # Check top 3
                if keyword.lower() in title_lower:
                    matching.append(narrative.narrative_id)
                    break
        
        return matching


# Export
__all__ = [
    'VigilAnalytics',
    'VigilAnalyticsPipeline',
]
