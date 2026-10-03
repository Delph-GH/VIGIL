"""
shared_analytics/salience/salience_scorer.py

Article salience (importance) scoring.

Extracted from both Vigil and Diaspora salience logic.

Measures:
- Recency (time-based decay)
- Entity prominence (key actors)
- Topic relevance
- Source authority
- Engagement signals
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

from shared_types import ScrapedArticle


class SalienceScorer:
    """
    Score article salience (importance/prominence).
    
    Combines multiple signals:
    - Recency: Recent articles score higher
    - Entity prominence: Articles mentioning key entities
    - Topic relevance: Coverage of important topics
    - Source authority: Trusted sources boost salience
    - Engagement: Views, shares, comments
    
    Usage:
        scorer = SalienceScorer(
            recency_weight=0.3,
            entity_weight=0.3,
            topic_weight=0.2,
            source_weight=0.1,
            engagement_weight=0.1,
        )
        
        score = scorer.score(article, entities=['Macron'], topics=['politique'])
        
        # Score: 0.0 - 1.0
        print(f"Salience: {score:.2f}")
    """
    
    def __init__(
        self,
        recency_weight: float = 0.3,
        entity_weight: float = 0.3,
        topic_weight: float = 0.2,
        source_weight: float = 0.1,
        engagement_weight: float = 0.1,
        recency_half_life_hours: float = 48.0,
    ):
        """
        Initialize salience scorer.
        
        Args:
            recency_weight: Weight for recency score
            entity_weight: Weight for entity prominence
            topic_weight: Weight for topic relevance
            source_weight: Weight for source authority
            engagement_weight: Weight for engagement signals
            recency_half_life_hours: Half-life for time decay
        """
        # Validate weights sum to 1.0
        total = (recency_weight + entity_weight + topic_weight + 
                source_weight + engagement_weight)
        
        if not math.isclose(total, 1.0, rel_tol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.recency_weight = recency_weight
        self.entity_weight = entity_weight
        self.topic_weight = topic_weight
        self.source_weight = source_weight
        self.engagement_weight = engagement_weight
        self.recency_half_life_hours = recency_half_life_hours
    
    def score(
        self,
        article: ScrapedArticle,
        important_entities: Optional[List[str]] = None,
        important_topics: Optional[List[str]] = None,
        trusted_sources: Optional[List[str]] = None,
        engagement_data: Optional[Dict] = None,
    ) -> float:
        """
        Calculate article salience score.
        
        Args:
            article: Article to score
            important_entities: List of important entity names
            important_topics: List of important topic keywords
            trusted_sources: List of trusted source names
            engagement_data: Dict with views, shares, comments
            
        Returns:
            Salience score (0.0 - 1.0)
        """
        # Calculate component scores
        recency = self._score_recency(article)
        entity_prominence = self._score_entity_prominence(
            article, important_entities or []
        )
        topic_relevance = self._score_topic_relevance(
            article, important_topics or []
        )
        source_authority = self._score_source_authority(
            article, trusted_sources or []
        )
        engagement = self._score_engagement(engagement_data or {})
        
        # Weighted combination
        salience = (
            self.recency_weight * recency +
            self.entity_weight * entity_prominence +
            self.topic_weight * topic_relevance +
            self.source_weight * source_authority +
            self.engagement_weight * engagement
        )
        
        return float(min(1.0, max(0.0, salience)))
    
    def _score_recency(self, article: ScrapedArticle) -> float:
        """
        Score based on article recency (exponential decay).
        
        Returns:
            Score (0.0 - 1.0), with 1.0 for very recent
        """
        if not article.scraped_at:
            return 0.5  # Default for unknown
        
        try:
            # Parse timestamp
            scraped_time = datetime.fromisoformat(
                article.scraped_at.replace('Z', '+00:00')
            )
            
            # Calculate age
            age_hours = (datetime.now(scraped_time.tzinfo) - scraped_time).total_seconds() / 3600
            
            # Exponential decay (half-life)
            score = math.exp(-math.log(2) * age_hours / self.recency_half_life_hours)
            
            return float(min(1.0, score))
        
        except Exception:
            return 0.5
    
    def _score_entity_prominence(
        self,
        article: ScrapedArticle,
        important_entities: List[str],
    ) -> float:
        """
        Score based on presence of important entities.
        
        Returns:
            Score (0.0 - 1.0)
        """
        if not important_entities:
            return 0.5  # Neutral if no entities specified
        
        # Extract text for analysis
        text = self._get_article_text(article).lower()
        
        # Count important entities mentioned
        mentions = 0
        for entity in important_entities:
            if entity.lower() in text:
                mentions += 1
        
        # Score: 0 = none, 1.0 = all important entities
        score = mentions / len(important_entities)
        
        return float(min(1.0, score))
    
    def _score_topic_relevance(
        self,
        article: ScrapedArticle,
        important_topics: List[str],
    ) -> float:
        """
        Score based on topic relevance.
        
        Returns:
            Score (0.0 - 1.0)
        """
        if not important_topics:
            return 0.5  # Neutral if no topics specified
        
        text = self._get_article_text(article).lower()
        
        # Count topic keyword matches
        matches = 0
        for topic in important_topics:
            if topic.lower() in text:
                matches += 1
        
        score = matches / len(important_topics)
        
        return float(min(1.0, score))
    
    def _score_source_authority(
        self,
        article: ScrapedArticle,
        trusted_sources: List[str],
    ) -> float:
        """
        Score based on source authority.
        
        Returns:
            Score (0.0 - 1.0)
        """
        if not trusted_sources:
            return 0.5  # Neutral if no trusted sources specified
        
        # Check if article is from trusted source
        source_name = article.source_name.lower()
        
        for trusted in trusted_sources:
            if trusted.lower() in source_name:
                return 1.0
        
        return 0.3  # Lower score for non-trusted sources
    
    def _score_engagement(self, engagement_data: Dict) -> float:
        """
        Score based on engagement signals.
        
        Args:
            engagement_data: Dict with views, shares, comments
            
        Returns:
            Score (0.0 - 1.0)
        """
        if not engagement_data:
            return 0.5  # Neutral if no engagement data
        
        # Extract metrics
        views = engagement_data.get('views', 0)
        shares = engagement_data.get('shares', 0)
        comments = engagement_data.get('comments', 0)
        
        # Simple engagement score
        # (in production, use normalization based on historical data)
        engagement_score = 0.0
        
        # Views (log scale)
        if views > 0:
            engagement_score += min(0.4, math.log10(views) / 5)
        
        # Shares (more valuable)
        if shares > 0:
            engagement_score += min(0.4, math.log10(shares + 1) / 3)
        
        # Comments (indicates discussion)
        if comments > 0:
            engagement_score += min(0.2, math.log10(comments + 1) / 2)
        
        return float(min(1.0, engagement_score))
    
    def _get_article_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
        parts = []
        
        if article.title:
            parts.append(article.title)
        
        if article.body_text:
            parts.append(article.body_text)
        
        return " ".join(parts)
    
    def score_batch(
        self,
        articles: List[ScrapedArticle],
        **kwargs,
    ) -> List[float]:
        """
        Score multiple articles.
        
        Args:
            articles: List of articles
            **kwargs: Arguments passed to score()
            
        Returns:
            List of salience scores
        """
        return [self.score(article, **kwargs) for article in articles]


# Export
__all__ = [
    'SalienceScorer',
]
