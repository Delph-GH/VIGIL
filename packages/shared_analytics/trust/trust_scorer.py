"""
shared_analytics/trust/trust_scorer.py

Source trust (reliability) scoring.

Extracted from both Vigil and Diaspora trust logic.

Measures:
- Historical accuracy
- Consistency over time
- Source reputation
- Verification status
- Hallucination rate
"""

from typing import Dict, List, Optional
from datetime import datetime
import math


class TrustScorer:
    """
    Score source trust (reliability/credibility).
    
    Combines multiple signals:
    - Historical accuracy: Past verification record
    - Consistency: Stable reporting over time
    - Source reputation: Established reliability
    - Verification status: Third-party validation
    - Hallucination rate: Low hallucination score
    
    Usage:
        scorer = TrustScorer(
            accuracy_weight=0.4,
            consistency_weight=0.2,
            reputation_weight=0.2,
            verification_weight=0.1,
            hallucination_weight=0.1,
        )
        
        score = scorer.score_source(
            source_name="Le Monde",
            accuracy_rate=0.95,
            consistency_score=0.88,
        )
        
        print(f"Trust: {score:.2f}")
    """
    
    def __init__(
        self,
        accuracy_weight: float = 0.4,
        consistency_weight: float = 0.2,
        reputation_weight: float = 0.2,
        verification_weight: float = 0.1,
        hallucination_weight: float = 0.1,
    ):
        """
        Initialize trust scorer.
        
        Args:
            accuracy_weight: Weight for historical accuracy
            consistency_weight: Weight for reporting consistency
            reputation_weight: Weight for source reputation
            verification_weight: Weight for verification status
            hallucination_weight: Weight for hallucination rate
        """
        # Validate weights
        total = (accuracy_weight + consistency_weight + reputation_weight +
                verification_weight + hallucination_weight)
        
        if not math.isclose(total, 1.0, rel_tol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.accuracy_weight = accuracy_weight
        self.consistency_weight = consistency_weight
        self.reputation_weight = reputation_weight
        self.verification_weight = verification_weight
        self.hallucination_weight = hallucination_weight
        
        # Known trusted sources (bootstrap)
        self.trusted_sources = {
            'le monde': 0.9,
            'le figaro': 0.85,
            'liberation': 0.85,
            'france 24': 0.88,
            'rfi': 0.87,
            'afp': 0.92,
            'reuters': 0.93,
            'bbc': 0.90,
        }
    
    def score_source(
        self,
        source_name: str,
        accuracy_rate: Optional[float] = None,
        consistency_score: Optional[float] = None,
        verification_status: Optional[str] = None,
        hallucination_rate: Optional[float] = None,
        article_count: Optional[int] = None,
    ) -> float:
        """
        Calculate source trust score.
        
        Args:
            source_name: Source name
            accuracy_rate: Historical accuracy (0-1)
            consistency_score: Reporting consistency (0-1)
            verification_status: 'verified', 'partial', 'unverified'
            hallucination_rate: Rate of hallucinations (0-1, lower better)
            article_count: Total articles from source
            
        Returns:
            Trust score (0.0 - 1.0)
        """
        # Component scores
        accuracy = self._score_accuracy(accuracy_rate)
        consistency = self._score_consistency(consistency_score, article_count)
        reputation = self._score_reputation(source_name)
        verification = self._score_verification(verification_status)
        hallucination = self._score_hallucination(hallucination_rate)
        
        # Weighted combination
        trust = (
            self.accuracy_weight * accuracy +
            self.consistency_weight * consistency +
            self.reputation_weight * reputation +
            self.verification_weight * verification +
            self.hallucination_weight * hallucination
        )
        
        return float(min(1.0, max(0.0, trust)))
    
    def _score_accuracy(self, accuracy_rate: Optional[float]) -> float:
        """
        Score historical accuracy.
        
        Args:
            accuracy_rate: Rate of accurate articles (0-1)
            
        Returns:
            Score (0.0 - 1.0)
        """
        if accuracy_rate is None:
            return 0.5  # Neutral for unknown
        
        # Accuracy directly maps to score
        return float(min(1.0, max(0.0, accuracy_rate)))
    
    def _score_consistency(
        self,
        consistency_score: Optional[float],
        article_count: Optional[int],
    ) -> float:
        """
        Score reporting consistency.
        
        Args:
            consistency_score: Consistency metric (0-1)
            article_count: Total articles (for confidence)
            
        Returns:
            Score (0.0 - 1.0)
        """
        if consistency_score is None:
            return 0.5
        
        score = consistency_score
        
        # Adjust based on sample size
        if article_count is not None and article_count < 10:
            # Lower confidence for small samples
            score *= 0.7
        
        return float(min(1.0, max(0.0, score)))
    
    def _score_reputation(self, source_name: str) -> float:
        """
        Score source reputation.
        
        Args:
            source_name: Source name
            
        Returns:
            Score (0.0 - 1.0)
        """
        # Check known trusted sources
        source_lower = source_name.lower()
        
        for trusted, score in self.trusted_sources.items():
            if trusted in source_lower:
                return score
        
        # Default score for unknown sources
        return 0.5
    
    def _score_verification(self, verification_status: Optional[str]) -> float:
        """
        Score verification status.
        
        Args:
            verification_status: 'verified', 'partial', 'unverified', None
            
        Returns:
            Score (0.0 - 1.0)
        """
        if verification_status is None:
            return 0.5
        
        status_scores = {
            'verified': 1.0,
            'partial': 0.7,
            'unverified': 0.3,
        }
        
        return status_scores.get(verification_status.lower(), 0.5)
    
    def _score_hallucination(self, hallucination_rate: Optional[float]) -> float:
        """
        Score based on hallucination rate (inverted).
        
        Args:
            hallucination_rate: Rate of hallucinations (0-1)
            
        Returns:
            Score (0.0 - 1.0), with 1.0 for zero hallucinations
        """
        if hallucination_rate is None:
            return 0.5
        
        # Invert: low hallucination = high score
        score = 1.0 - hallucination_rate
        
        return float(min(1.0, max(0.0, score)))
    
    def add_trusted_source(self, source_name: str, trust_score: float):
        """
        Add or update a trusted source.
        
        Args:
            source_name: Source name
            trust_score: Trust score (0-1)
        """
        self.trusted_sources[source_name.lower()] = trust_score
    
    def score_sources_batch(
        self,
        sources: List[Dict],
    ) -> List[float]:
        """
        Score multiple sources.
        
        Args:
            sources: List of source dicts with scoring params
            
        Returns:
            List of trust scores
        """
        scores = []
        
        for source_data in sources:
            score = self.score_source(**source_data)
            scores.append(score)
        
        return scores


# Export
__all__ = [
    'TrustScorer',
]
