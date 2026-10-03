"""
shared_analytics/personas/base_persona.py

Base persona framework for content-persona matching.

Abstract foundation that platforms extend with specific profiles.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from shared_types import ScrapedArticle


@dataclass
class PersonaProfile:
    """
    Persona profile structure.
    
    Attributes:
        persona_id: Unique identifier
        name: Persona name
        description: Persona description
        interests: Key interests/topics
        keywords: Relevant keywords
        excluded_keywords: Keywords to avoid
        preferred_sources: Preferred sources
        demographic: Demographic info (optional)
        metadata: Additional metadata
    """
    persona_id: str
    name: str
    description: str
    interests: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    excluded_keywords: List[str] = field(default_factory=list)
    preferred_sources: List[str] = field(default_factory=list)
    demographic: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'persona_id': self.persona_id,
            'name': self.name,
            'description': self.description,
            'interests': self.interests,
            'keywords': self.keywords,
            'excluded_keywords': self.excluded_keywords,
            'preferred_sources': self.preferred_sources,
            'demographic': self.demographic,
            'metadata': self.metadata,
        }


@dataclass
class ContentMatch:
    """
    Content-persona match result.
    
    Attributes:
        persona_id: Matched persona
        article_id: Matched article
        match_score: Overall match score (0-1)
        interest_score: Interest relevance (0-1)
        keyword_score: Keyword match (0-1)
        source_score: Source preference (0-1)
        exclusion_penalty: Penalty for excluded keywords
        reasons: Match reasons
    """
    persona_id: str
    article_id: str
    match_score: float
    interest_score: float = 0.0
    keyword_score: float = 0.0
    source_score: float = 0.0
    exclusion_penalty: float = 0.0
    reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'persona_id': self.persona_id,
            'article_id': self.article_id,
            'match_score': self.match_score,
            'interest_score': self.interest_score,
            'keyword_score': self.keyword_score,
            'source_score': self.source_score,
            'exclusion_penalty': self.exclusion_penalty,
            'reasons': self.reasons,
        }


class BasePersona(ABC):
    """
    Abstract base class for personas.
    
    Platforms extend this with specific persona implementations.
    
    Example:
        class PoliticalPersona(BasePersona):
            def load_profiles(self):
                # Load political persona profiles
                pass
            
            def calculate_interest_score(self, article, profile):
                # Calculate political interest score
                pass
    """
    
    def __init__(self):
        """Initialize persona."""
        self.profiles: Dict[str, PersonaProfile] = {}
        self.load_profiles()
    
    @abstractmethod
    def load_profiles(self):
        """
        Load persona profiles.
        
        Platforms implement this to load their specific profiles.
        """
        pass
    
    def get_profile(self, persona_id: str) -> Optional[PersonaProfile]:
        """
        Get persona profile.
        
        Args:
            persona_id: Persona identifier
            
        Returns:
            PersonaProfile or None
        """
        return self.profiles.get(persona_id)
    
    def list_profiles(self) -> List[PersonaProfile]:
        """
        List all persona profiles.
        
        Returns:
            List of profiles
        """
        return list(self.profiles.values())
    
    @abstractmethod
    def calculate_interest_score(
        self,
        article: ScrapedArticle,
        profile: PersonaProfile,
    ) -> float:
        """
        Calculate interest relevance score.
        
        Platforms implement this with domain-specific logic.
        
        Args:
            article: Article to score
            profile: Persona profile
            
        Returns:
            Interest score (0-1)
        """
        pass
    
    def calculate_keyword_score(
        self,
        article: ScrapedArticle,
        profile: PersonaProfile,
    ) -> float:
        """
        Calculate keyword match score.
        
        Default implementation (can be overridden).
        
        Args:
            article: Article to score
            profile: Persona profile
            
        Returns:
            Keyword score (0-1)
        """
        if not profile.keywords:
            return 0.5  # Neutral
        
        # Get article text
        text = self._get_article_text(article).lower()
        
        # Count keyword matches
        matches = 0
        for keyword in profile.keywords:
            if keyword.lower() in text:
                matches += 1
        
        # Calculate score
        score = matches / len(profile.keywords)
        
        return min(1.0, score)
    
    def calculate_source_score(
        self,
        article: ScrapedArticle,
        profile: PersonaProfile,
    ) -> float:
        """
        Calculate source preference score.
        
        Default implementation (can be overridden).
        
        Args:
            article: Article to score
            profile: Persona profile
            
        Returns:
            Source score (0-1)
        """
        if not profile.preferred_sources:
            return 0.5  # Neutral
        
        # Check if article source is preferred
        source_name = article.source_name.lower()
        
        for preferred in profile.preferred_sources:
            if preferred.lower() in source_name:
                return 1.0
        
        return 0.3  # Not preferred but not excluded
    
    def calculate_exclusion_penalty(
        self,
        article: ScrapedArticle,
        profile: PersonaProfile,
    ) -> float:
        """
        Calculate penalty for excluded keywords.
        
        Default implementation (can be overridden).
        
        Args:
            article: Article to score
            profile: Persona profile
            
        Returns:
            Penalty (0-1, higher = worse)
        """
        if not profile.excluded_keywords:
            return 0.0  # No penalty
        
        # Get article text
        text = self._get_article_text(article).lower()
        
        # Count excluded keyword matches
        matches = 0
        for keyword in profile.excluded_keywords:
            if keyword.lower() in text:
                matches += 1
        
        # Calculate penalty
        penalty = matches / len(profile.excluded_keywords)
        
        return min(1.0, penalty)
    
    def _get_article_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
        parts = []
        
        if article.title:
            parts.append(article.title)
        
        if article.body_text:
            parts.append(article.body_text)
        
        return " ".join(parts)


# Export
__all__ = [
    'PersonaProfile',
    'ContentMatch',
    'BasePersona',
]
