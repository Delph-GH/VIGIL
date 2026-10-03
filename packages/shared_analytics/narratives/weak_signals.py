"""
shared_analytics/narratives/weak_signals.py

Weak signal detection for early warnings.

Identifies early indicators before they become mainstream narratives.
"""

from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import math

from shared_types import ScrapedArticle


class WeakSignal:
    """
    Represents a detected weak signal.
    
    Attributes:
        signal_id: Unique identifier
        keywords: Signal keywords
        article_count: Number of articles
        first_seen: First appearance
        amplification_rate: Growth rate
        sources: Diversity of sources
        is_novel: Whether signal is novel
    """
    
    def __init__(
        self,
        signal_id: str,
        keywords: List[str],
        article_count: int,
        first_seen: str,
        amplification_rate: float = 0.0,
        sources: Optional[List[str]] = None,
        is_novel: bool = False,
    ):
        self.signal_id = signal_id
        self.keywords = keywords
        self.article_count = article_count
        self.first_seen = first_seen
        self.amplification_rate = amplification_rate
        self.sources = sources or []
        self.is_novel = is_novel
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'signal_id': self.signal_id,
            'keywords': self.keywords,
            'article_count': self.article_count,
            'first_seen': self.first_seen,
            'amplification_rate': self.amplification_rate,
            'source_diversity': len(self.sources),
            'is_novel': self.is_novel,
        }


class WeakSignalDetector:
    """
    Detect weak signals (early indicators).
    
    Identifies:
    - Novel emerging topics
    - Fringe-to-mainstream transitions
    - Anomalous patterns
    - Amplification signals
    
    Usage:
        detector = WeakSignalDetector(
            min_articles=2,
            max_articles=10,
        )
        
        signals = detector.detect_signals(
            articles,
            baseline_keywords=baseline,
        )
        
        for signal in signals:
            print(f"Signal: {signal.keywords}")
            print(f"Rate: {signal.amplification_rate:.2f}")
    """
    
    def __init__(
        self,
        min_articles: int = 2,
        max_articles: int = 10,
        novelty_threshold: float = 0.7,
    ):
        """
        Initialize detector.
        
        Args:
            min_articles: Minimum articles for signal
            max_articles: Maximum (beyond = mainstream)
            novelty_threshold: Novelty threshold (0-1)
        """
        self.min_articles = min_articles
        self.max_articles = max_articles
        self.novelty_threshold = novelty_threshold
    
    def detect_signals(
        self,
        articles: List[ScrapedArticle],
        baseline_keywords: Optional[List[str]] = None,
        previous_period_articles: Optional[List[ScrapedArticle]] = None,
    ) -> List[WeakSignal]:
        """
        Detect weak signals in articles.
        
        Args:
            articles: Current period articles
            baseline_keywords: Known mainstream keywords
            previous_period_articles: Previous period for comparison
            
        Returns:
            List of weak signals
        """
        if not articles:
            return []
        
        # Extract keywords
        keyword_articles = self._extract_keyword_clusters(articles)
        
        signals = []
        
        for keywords, article_list in keyword_articles.items():
            # Check article count range
            if len(article_list) < self.min_articles:
                continue
            
            if len(article_list) > self.max_articles:
                continue  # Too mainstream
            
            # Check novelty
            is_novel = self._is_novel(keywords, baseline_keywords)
            
            # Calculate amplification
            amplification = self._calculate_amplification(
                keywords,
                article_list,
                previous_period_articles,
            )
            
            # Get sources
            sources = list(set(a.source_name for a in article_list))
            
            # Create signal
            signal = WeakSignal(
                signal_id=f"signal_{'_'.join(keywords[:2])}",
                keywords=list(keywords),
                article_count=len(article_list),
                first_seen=min(a.scraped_at for a in article_list if a.scraped_at),
                amplification_rate=amplification,
                sources=sources,
                is_novel=is_novel,
            )
            
            signals.append(signal)
        
        # Sort by amplification rate
        signals.sort(key=lambda s: s.amplification_rate, reverse=True)
        
        return signals
    
    def _extract_keyword_clusters(
        self,
        articles: List[ScrapedArticle],
    ) -> Dict[Tuple[str, ...], List[ScrapedArticle]]:
        """Group articles by keyword combinations."""
        clusters = defaultdict(list)
        
        for article in articles:
            if not article.title:
                continue
            
            # Extract keywords
            keywords = self._extract_keywords(article.title)
            
            if len(keywords) < 2:
                continue
            
            # Use top 2-3 keywords as cluster key
            key = tuple(sorted(keywords[:3]))
            clusters[key].append(article)
        
        return dict(clusters)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        words = text.lower().split()
        
        stopwords = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une',
                     'et', 'ou', 'à', 'en', 'pour', 'par', 'sur'}
        
        return [w for w in words if len(w) > 3 and w not in stopwords]
    
    def _is_novel(
        self,
        keywords: Tuple[str, ...],
        baseline_keywords: Optional[List[str]],
    ) -> bool:
        """Check if keywords are novel (not in baseline)."""
        if not baseline_keywords:
            return True
        
        baseline_set = set(baseline_keywords)
        keyword_set = set(keywords)
        
        # Calculate novelty
        overlap = len(keyword_set & baseline_set)
        novelty = 1.0 - (overlap / len(keyword_set))
        
        return novelty >= self.novelty_threshold
    
    def _calculate_amplification(
        self,
        keywords: Tuple[str, ...],
        current_articles: List[ScrapedArticle],
        previous_articles: Optional[List[ScrapedArticle]],
    ) -> float:
        """Calculate amplification rate."""
        if not previous_articles:
            return 1.0  # New signal
        
        # Count occurrences in previous period
        prev_count = 0
        
        for article in previous_articles:
            if not article.title:
                continue
            
            article_keywords = set(self._extract_keywords(article.title))
            keyword_set = set(keywords)
            
            if len(keyword_set & article_keywords) >= 2:
                prev_count += 1
        
        # Calculate growth
        current_count = len(current_articles)
        
        if prev_count == 0:
            return float('inf')  # New appearance
        
        return current_count / prev_count


# Export
__all__ = [
    'WeakSignal',
    'WeakSignalDetector',
]
