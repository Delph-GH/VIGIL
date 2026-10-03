"""
shared_analytics/narratives/detector.py

Narrative detection from article clusters.

Identifies emergent narratives by clustering articles and extracting themes.
"""

from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import math

from shared_types import ScrapedArticle


class Narrative:
    """
    Represents a detected narrative.
    
    Attributes:
        narrative_id: Unique identifier
        theme: Main theme/topic
        keywords: Key terms
        article_ids: Articles in narrative
        strength: Narrative strength (0-1)
        first_seen: First appearance
        last_seen: Last appearance
        actors: Key entities/actors
    """
    
    def __init__(
        self,
        narrative_id: str,
        theme: str,
        keywords: List[str],
        article_ids: List[str],
        strength: float = 0.0,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        actors: Optional[List[str]] = None,
    ):
        self.narrative_id = narrative_id
        self.theme = theme
        self.keywords = keywords
        self.article_ids = article_ids
        self.strength = strength
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.actors = actors or []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'narrative_id': self.narrative_id,
            'theme': self.theme,
            'keywords': self.keywords,
            'article_count': len(self.article_ids),
            'strength': self.strength,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'actors': self.actors,
        }


class NarrativeDetector:
    """
    Detect narratives from article collections.
    
    Identifies emergent narratives by:
    - Clustering similar articles
    - Extracting common themes
    - Measuring narrative strength
    - Tracking key actors
    
    Usage:
        detector = NarrativeDetector(min_articles=3)
        
        narratives = detector.detect_narratives(articles)
        
        for narrative in narratives:
            print(f"Theme: {narrative.theme}")
            print(f"Strength: {narrative.strength:.2f}")
            print(f"Keywords: {narrative.keywords}")
    """
    
    def __init__(
        self,
        min_articles: int = 3,
        min_keyword_freq: int = 2,
        max_narratives: int = 20,
    ):
        """
        Initialize detector.
        
        Args:
            min_articles: Minimum articles for narrative
            min_keyword_freq: Minimum keyword frequency
            max_narratives: Maximum narratives to return
        """
        self.min_articles = min_articles
        self.min_keyword_freq = min_keyword_freq
        self.max_narratives = max_narratives
    
    def detect_narratives(
        self,
        articles: List[ScrapedArticle],
        article_clusters: Optional[Dict[int, List[str]]] = None,
    ) -> List[Narrative]:
        """
        Detect narratives from articles.
        
        Args:
            articles: List of articles
            article_clusters: Optional pre-computed clusters {cluster_id: [article_ids]}
            
        Returns:
            List of detected narratives
        """
        if not articles:
            return []
        
        # If no clusters provided, create simple keyword-based clusters
        if article_clusters is None:
            article_clusters = self._cluster_by_keywords(articles)
        
        # Extract narratives from clusters
        narratives = []
        
        for cluster_id, article_ids in article_clusters.items():
            # Skip small clusters
            if len(article_ids) < self.min_articles:
                continue
            
            # Get articles in cluster
            cluster_articles = [a for a in articles if a.article_id in article_ids]
            
            if not cluster_articles:
                continue
            
            # Extract narrative
            narrative = self._extract_narrative(
                cluster_id=str(cluster_id),
                articles=cluster_articles,
            )
            
            if narrative:
                narratives.append(narrative)
        
        # Sort by strength and limit
        narratives.sort(key=lambda n: n.strength, reverse=True)
        
        return narratives[:self.max_narratives]
    
    def _cluster_by_keywords(
        self,
        articles: List[ScrapedArticle],
    ) -> Dict[int, List[str]]:
        """
        Simple keyword-based clustering.
        
        Args:
            articles: List of articles
            
        Returns:
            Dictionary of clusters {cluster_id: [article_ids]}
        """
        # Extract keywords from each article
        article_keywords = {}
        
        for article in articles:
            keywords = self._extract_keywords(article)
            article_keywords[article.article_id] = set(keywords)
        
        # Simple clustering: group by shared keywords
        clusters = defaultdict(list)
        cluster_id = 0
        assigned = set()
        
        for article in articles:
            if article.article_id in assigned:
                continue
            
            # Start new cluster
            cluster = [article.article_id]
            assigned.add(article.article_id)
            
            article_kw = article_keywords[article.article_id]
            
            # Find similar articles
            for other in articles:
                if other.article_id in assigned:
                    continue
                
                other_kw = article_keywords[other.article_id]
                
                # Check keyword overlap
                overlap = len(article_kw & other_kw)
                
                if overlap >= 2:  # At least 2 shared keywords
                    cluster.append(other.article_id)
                    assigned.add(other.article_id)
            
            if len(cluster) >= self.min_articles:
                clusters[cluster_id] = cluster
                cluster_id += 1
        
        return dict(clusters)
    
    def _extract_narrative(
        self,
        cluster_id: str,
        articles: List[ScrapedArticle],
    ) -> Optional[Narrative]:
        """
        Extract narrative from article cluster.
        
        Args:
            cluster_id: Cluster identifier
            articles: Articles in cluster
            
        Returns:
            Narrative or None
        """
        if not articles:
            return None
        
        # Extract keywords across all articles
        all_keywords = []
        for article in articles:
            keywords = self._extract_keywords(article)
            all_keywords.extend(keywords)
        
        # Find most common keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = [
            kw for kw, count in keyword_counts.most_common(10)
            if count >= self.min_keyword_freq
        ]
        
        if not top_keywords:
            return None
        
        # Create theme from top keywords
        theme = " + ".join(top_keywords[:3])
        
        # Calculate strength
        strength = self._calculate_strength(articles, keyword_counts)
        
        # Extract timestamps
        timestamps = [a.scraped_at for a in articles if a.scraped_at]
        first_seen = min(timestamps) if timestamps else None
        last_seen = max(timestamps) if timestamps else None
        
        # Extract actors (simple entity extraction from titles)
        actors = self._extract_actors(articles)
        
        return Narrative(
            narrative_id=f"narrative_{cluster_id}",
            theme=theme,
            keywords=top_keywords,
            article_ids=[a.article_id for a in articles],
            strength=strength,
            first_seen=first_seen,
            last_seen=last_seen,
            actors=actors,
        )
    
    def _extract_keywords(self, article: ScrapedArticle) -> List[str]:
        """Extract keywords from article."""
        # Simple extraction: split title and filter
        if not article.title:
            return []
        
        # Simple tokenization
        words = article.title.lower().split()
        
        # Filter short words and common stopwords
        stopwords = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 
                     'et', 'ou', 'à', 'en', 'pour', 'par', 'sur', 'dans'}
        
        keywords = [
            w for w in words 
            if len(w) > 3 and w not in stopwords
        ]
        
        return keywords[:10]  # Top 10
    
    def _calculate_strength(
        self,
        articles: List[ScrapedArticle],
        keyword_counts: Counter,
    ) -> float:
        """
        Calculate narrative strength.
        
        Factors:
        - Number of articles
        - Keyword concentration
        - Recency
        """
        # Article count factor (log scale)
        article_factor = min(1.0, math.log10(len(articles) + 1) / 2)
        
        # Keyword concentration (how focused is the narrative)
        total_keywords = sum(keyword_counts.values())
        top_keywords_count = sum(count for _, count in keyword_counts.most_common(5))
        concentration = top_keywords_count / total_keywords if total_keywords > 0 else 0
        
        # Recency factor
        recency = self._calculate_recency(articles)
        
        # Weighted combination
        strength = 0.4 * article_factor + 0.3 * concentration + 0.3 * recency
        
        return min(1.0, max(0.0, strength))
    
    def _calculate_recency(self, articles: List[ScrapedArticle]) -> float:
        """Calculate recency score."""
        timestamps = [a.scraped_at for a in articles if a.scraped_at]
        
        if not timestamps:
            return 0.5
        
        try:
            # Get most recent article
            most_recent = max(timestamps)
            recent_time = datetime.fromisoformat(most_recent.replace('Z', '+00:00'))
            now = datetime.now(recent_time.tzinfo)
            
            # Hours since most recent
            hours_ago = (now - recent_time).total_seconds() / 3600
            
            # Exponential decay (48hr half-life)
            recency = math.exp(-math.log(2) * hours_ago / 48)
            
            return min(1.0, recency)
        
        except Exception:
            return 0.5
    
    def _extract_actors(self, articles: List[ScrapedArticle]) -> List[str]:
        """Extract key actors (simple capitalized word extraction)."""
        # Simple approach: find capitalized words in titles
        actors = []
        
        for article in articles:
            if not article.title:
                continue
            
            words = article.title.split()
            
            # Find capitalized words (likely proper nouns)
            for word in words:
                if word and word[0].isupper() and len(word) > 3:
                    actors.append(word)
        
        # Count and return top actors
        actor_counts = Counter(actors)
        return [actor for actor, _ in actor_counts.most_common(5)]


# Export
__all__ = [
    'Narrative',
    'NarrativeDetector',
]
