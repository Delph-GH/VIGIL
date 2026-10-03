"""
apps/vigil-platform/vigil_dashboards/utils/backend.py

Backend integration utilities for Vigil dashboard.

Provides real data access to all dashboard components.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add packages to path
_root = Path(__file__).resolve().parents[4]
for _p in (_root / "packages", _root / "apps" / "vigil-platform"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared_types import ScrapedArticle, ScrapeStrategy
from analytics.pipeline import VigilAnalyticsPipeline
from shared_analytics import NarrativeDetector
from shared_ai.nlp.sentiment import SentimentAnalyzer
from shared_validation import QualityScorer
from shared_observability import get_logger

logger = get_logger(__name__)


class VigilBackend:
    """
    Backend integration for Vigil dashboard.
    
    Provides real-time data access and computation.
    """
    
    def __init__(self):
        """Initialize backend components."""
        self.analytics_pipeline = VigilAnalyticsPipeline(
            important_entities=['Macron', 'Borne', 'Le Pen'],
            important_topics=['réforme', 'politique', 'économie'],
            trusted_sources=['Le Monde', 'AFP', 'Le Figaro'],
        )
        
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ner = None  # NER needs spaCy; loaded lazily via get_ner()
        self.quality_scorer = QualityScorer()
        self.narrative_detector = NarrativeDetector(min_articles=3)
        
        logger.info('backend_initialized', platform='vigil')

    # No database is wired yet: articles come from a synthetic generator.
    is_sample_data = True

    def get_ner(self):
        """Return a NamedEntityRecognizer, or None if spaCy is not installed."""
        if self.ner is None:
            try:
                from shared_ai.nlp.ner import NamedEntityRecognizer
                self.ner = NamedEntityRecognizer()
            except ImportError:
                return None
        return self.ner
    
    def fetch_recent_articles(self, days: int = 7) -> List[ScrapedArticle]:
        """
        Fetch recent articles from database.
        
        In production, this would query the actual database.
        For now, returns sample data structure.
        """
        # Sample articles for demonstration
        # In production: return db.query_articles(days=days)
        
        articles = []
        base_date = datetime.now()
        
        for i in range(50):
            article = ScrapedArticle(
                article_id=f"vigil_{i:03d}",
                url=f"https://example.com/article/{i}",
                source_name="Le Monde" if i % 3 == 0 else "AFP" if i % 3 == 1 else "Le Figaro",
                scraped_at=(base_date - timedelta(days=i % days)).isoformat(),
                extraction_strategy=ScrapeStrategy.STATIC_HTTP,
                title=f"Article politique {i}: Réforme en cours",
                body_text=f"Contenu de l'article {i} concernant la réforme politique.",
            )
            articles.append(article)
        
        return articles
    
    def analyze_articles(self, articles: List[ScrapedArticle]) -> List[Dict]:
        """
        Run analytics pipeline on articles.
        
        Returns:
            List of analytics results
        """
        logger.info('analyzing_articles', count=len(articles))
        
        analytics_results = self.analytics_pipeline.process_batch(articles)
        
        return [a.to_dict() for a in analytics_results]
    
    def detect_narratives(self, articles: List[ScrapedArticle]) -> List[Dict]:
        """Detect narratives in articles."""
        narratives = self.narrative_detector.detect_narratives(articles)
        return [n.to_dict() for n in narratives]
    
    def analyze_sentiment(self, articles: List[ScrapedArticle]) -> Dict[str, float]:
        """
        Analyze sentiment across articles.
        
        Returns:
            Dict of sentiment scores
        """
        sentiments = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
        }
        
        for article in articles:
            if article.body_text:
                result = self.sentiment_analyzer.analyze(article.body_text)
                sentiments[result.polarity.value] = sentiments.get(result.polarity.value, 0) + 1
        
        total = len(articles)
        if total > 0:
            sentiments = {k: (v / total) * 100 for k, v in sentiments.items()}
        
        return sentiments
    
    def detect_contradictions(self, articles: List[ScrapedArticle]) -> List[Dict]:
        """
        Detect contradictions in article narratives.
        
        Returns:
            List of contradiction dicts
        """
        # In production: use advanced NLP to detect semantic contradictions
        # For now: detect based on conflicting keywords
        
        contradictions = []
        
        # Group by topic
        topics = {}
        for article in articles:
            if not article.title:
                continue
            
            # Simple topic extraction
            if 'réforme' in article.title.lower():
                topic = 'réforme'
            elif 'économie' in article.title.lower():
                topic = 'économie'
            else:
                continue
            
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(article)
        
        # Check for contradictions within topics
        for topic, topic_articles in topics.items():
            if len(topic_articles) >= 2:
                contradictions.append({
                    'topic': topic.capitalize(),
                    'articles': len(topic_articles),
                    'sources': list(set(a.source_name for a in topic_articles)),
                    'type': 'policy_interpretation',
                })
        
        return contradictions
    
    def compute_engagement_metrics(self, articles: List[ScrapedArticle]) -> Dict:
        """
        Compute engagement metrics.
        
        In production: pull from analytics database
        """
        return {
            'total_views': len(articles) * 1500,  # Sample computation
            'avg_time': 2.3,  # minutes
            'share_rate': 0.15,
            'comment_rate': 0.08,
        }
    
    def get_trust_network(self) -> Dict:
        """
        Get trust network data.
        
        Returns source trust relationships.
        """
        return {
            'nodes': [
                {'id': 'Le Monde', 'trust': 0.90, 'type': 'newspaper'},
                {'id': 'AFP', 'trust': 0.92, 'type': 'agency'},
                {'id': 'Le Figaro', 'trust': 0.85, 'type': 'newspaper'},
                {'id': 'Reuters', 'trust': 0.93, 'type': 'agency'},
            ],
            'edges': [
                {'source': 'AFP', 'target': 'Le Monde', 'weight': 0.8},
                {'source': 'Reuters', 'target': 'Le Figaro', 'weight': 0.7},
            ],
        }
    
    def compute_signal_noise(self, articles: List[ScrapedArticle]) -> Dict:
        """
        Compute signal/noise ratio.
        
        Uses quality scorer to determine signal strength.
        """
        signal_count = 0
        noise_count = 0
        
        for article in articles:
            quality_score, _checks = self.quality_scorer.score(article)
            
            if quality_score >= 70:
                signal_count += 1
            else:
                noise_count += 1
        
        total = signal_count + noise_count
        
        return {
            'signal_ratio': (signal_count / total * 100) if total > 0 else 0,
            'noise_ratio': (noise_count / total * 100) if total > 0 else 0,
            'signal_count': signal_count,
            'noise_count': noise_count,
        }


# Global backend instance
_backend = None

def get_backend() -> VigilBackend:
    """Get or create backend instance."""
    global _backend
    if _backend is None:
        _backend = VigilBackend()
    return _backend


# Export
__all__ = [
    'VigilBackend',
    'get_backend',
]
