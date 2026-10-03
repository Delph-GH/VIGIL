"""
shared_analytics/personas/modeling_engine.py

Persona modeling engine for content-persona matching.

Core logic for matching content to personas.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from shared_types import ScrapedArticle
from .base_persona import BasePersona, PersonaProfile, ContentMatch


class PersonaModelingEngine:
    """
    Core persona modeling engine.
    
    Matches content to personas using:
    - Interest scoring
    - Keyword matching
    - Source preferences
    - Exclusion rules
    
    Usage:
        # Initialize with platform persona
        engine = PersonaModelingEngine(
            persona=political_persona,
            interest_weight=0.4,
            keyword_weight=0.3,
            source_weight=0.2,
            exclusion_weight=0.1,
        )
        
        # Match article to personas
        matches = engine.match_article(article, top_k=3)
        
        # Get best match
        best = matches[0]
        print(f"Best persona: {best.persona_id}")
        print(f"Score: {best.match_score:.2f}")
    """
    
    def __init__(
        self,
        persona: BasePersona,
        interest_weight: float = 0.4,
        keyword_weight: float = 0.3,
        source_weight: float = 0.2,
        exclusion_weight: float = 0.1,
        min_score: float = 0.3,
    ):
        """
        Initialize modeling engine.
        
        Args:
            persona: Platform persona implementation
            interest_weight: Weight for interest score
            keyword_weight: Weight for keyword score
            source_weight: Weight for source score
            exclusion_weight: Weight for exclusion penalty
            min_score: Minimum score threshold
        """
        self.persona = persona
        self.interest_weight = interest_weight
        self.keyword_weight = keyword_weight
        self.source_weight = source_weight
        self.exclusion_weight = exclusion_weight
        self.min_score = min_score
        
        # Validate weights
        total = (interest_weight + keyword_weight + 
                source_weight + exclusion_weight)
        
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def match_article(
        self,
        article: ScrapedArticle,
        top_k: Optional[int] = None,
        include_reasons: bool = True,
    ) -> List[ContentMatch]:
        """
        Match article to personas.
        
        Args:
            article: Article to match
            top_k: Return top K matches (None = all)
            include_reasons: Include match reasons
            
        Returns:
            List of ContentMatch, sorted by score
        """
        matches = []
        
        # Try each persona profile
        for profile in self.persona.list_profiles():
            match = self._calculate_match(
                article,
                profile,
                include_reasons=include_reasons,
            )
            
            # Filter by minimum score
            if match.match_score >= self.min_score:
                matches.append(match)
        
        # Sort by score
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        # Limit to top K
        if top_k is not None:
            matches = matches[:top_k]
        
        return matches
    
    def match_articles_batch(
        self,
        articles: List[ScrapedArticle],
        top_k: Optional[int] = 1,
    ) -> Dict[str, List[ContentMatch]]:
        """
        Match multiple articles.
        
        Args:
            articles: Articles to match
            top_k: Top matches per article
            
        Returns:
            Dictionary {article_id: [matches]}
        """
        results = {}
        
        for article in articles:
            matches = self.match_article(article, top_k=top_k)
            results[article.article_id] = matches
        
        return results
    
    def segment_articles(
        self,
        articles: List[ScrapedArticle],
        persona_id: str,
    ) -> List[ScrapedArticle]:
        """
        Segment articles for specific persona.
        
        Args:
            articles: Articles to segment
            persona_id: Target persona
            
        Returns:
            Articles matching persona
        """
        matching = []
        
        profile = self.persona.get_profile(persona_id)
        
        if not profile:
            return []
        
        for article in articles:
            match = self._calculate_match(article, profile)
            
            if match.match_score >= self.min_score:
                matching.append(article)
        
        return matching
    
    def get_persona_distribution(
        self,
        articles: List[ScrapedArticle],
    ) -> Dict[str, int]:
        """
        Get distribution of articles across personas.
        
        Args:
            articles: Articles to analyze
            
        Returns:
            Dictionary {persona_id: count}
        """
        distribution = {}
        
        for article in articles:
            matches = self.match_article(article, top_k=1)
            
            if matches:
                persona_id = matches[0].persona_id
                distribution[persona_id] = distribution.get(persona_id, 0) + 1
        
        return distribution
    
    def _calculate_match(
        self,
        article: ScrapedArticle,
        profile: PersonaProfile,
        include_reasons: bool = False,
    ) -> ContentMatch:
        """
        Calculate match for article-profile pair.
        
        Args:
            article: Article
            profile: Persona profile
            include_reasons: Include match reasons
            
        Returns:
            ContentMatch
        """
        # Calculate component scores
        interest_score = self.persona.calculate_interest_score(article, profile)
        keyword_score = self.persona.calculate_keyword_score(article, profile)
        source_score = self.persona.calculate_source_score(article, profile)
        exclusion_penalty = self.persona.calculate_exclusion_penalty(article, profile)
        
        # Weighted combination
        match_score = (
            self.interest_weight * interest_score +
            self.keyword_weight * keyword_score +
            self.source_weight * source_score -
            self.exclusion_weight * exclusion_penalty
        )
        
        # Ensure in range [0, 1]
        match_score = max(0.0, min(1.0, match_score))
        
        # Build reasons
        reasons = []
        
        if include_reasons:
            if interest_score > 0.6:
                reasons.append(f"High interest relevance ({interest_score:.2f})")
            
            if keyword_score > 0.6:
                reasons.append(f"Strong keyword match ({keyword_score:.2f})")
            
            if source_score > 0.8:
                reasons.append("Preferred source")
            
            if exclusion_penalty > 0.3:
                reasons.append(f"Contains excluded keywords (penalty: {exclusion_penalty:.2f})")
        
        return ContentMatch(
            persona_id=profile.persona_id,
            article_id=article.article_id,
            match_score=match_score,
            interest_score=interest_score,
            keyword_score=keyword_score,
            source_score=source_score,
            exclusion_penalty=exclusion_penalty,
            reasons=reasons,
        )


# Export
__all__ = [
    'PersonaModelingEngine',
]
