"""
shared_ai/nlp/sentiment.py

Sentiment analysis for French political content.

Extracted from Vigil's processing/nlp/sentiment.py

Simple rule-based sentiment analysis.
For production, consider using pre-trained models or APIs.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SentimentPolarity(str, Enum):
    """Sentiment polarity."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """
    Sentiment analysis result.
    
    Attributes:
        score: Sentiment score (-1.0 to +1.0)
        polarity: Sentiment polarity
        confidence: Confidence score (0-1)
        subjectivity: Subjectivity score (0-1)
    """
    score: float
    polarity: SentimentPolarity
    confidence: float = 0.5
    subjectivity: float = 0.5


class SentimentAnalyzer:
    """
    Simple rule-based sentiment analyzer for French text.
    
    NOTE: This is a basic implementation. For production use:
    - Consider using transformers (CamemBERT, FlauBERT)
    - Or external APIs (Google Cloud NLP, AWS Comprehend)
    
    Usage:
        analyzer = SentimentAnalyzer()
        
        result = analyzer.analyze(text)
        
        print(f"Sentiment: {result.polarity.value}")
        print(f"Score: {result.score:.2f}")
    """
    
    def __init__(self, language: str = "fr"):
        """
        Initialize sentiment analyzer.
        
        Args:
            language: Language code (fr, en, de)
        """
        self.language = language
        
        # Load sentiment lexicons
        self._load_lexicons()
    
    def _load_lexicons(self):
        """Load sentiment lexicons for language."""
        # Simple French sentiment lexicon
        # In production, use a comprehensive lexicon or model
        
        self.positive_words = {
            # Positive French words
            'bon', 'bien', 'excellent', 'positif', 'succès', 'réussite',
            'progrès', 'amélioration', 'favorable', 'optimiste', 'victoire',
            'gagner', 'efficace', 'important', 'fort', 'grand', 'meilleur',
        }
        
        self.negative_words = {
            # Negative French words
            'mauvais', 'mal', 'problème', 'échec', 'erreur', 'danger',
            'risque', 'crise', 'défaite', 'perdre', 'faible', 'grave',
            'difficile', 'impossible', 'catastrophe', 'scandale', 'corruption',
        }
        
        # Intensifiers
        self.intensifiers = {
            'très', 'vraiment', 'extrêmement', 'particulièrement',
            'trop', 'assez', 'plutôt',
        }
        
        # Negations
        self.negations = {
            'ne', 'pas', 'non', 'jamais', 'rien', 'aucun',
        }
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text
            
        Returns:
            SentimentResult
        """
        if not text:
            return SentimentResult(
                score=0.0,
                polarity=SentimentPolarity.NEUTRAL,
            )
        
        # Tokenize (simple split)
        tokens = text.lower().split()
        
        # Count sentiment words
        positive_count = sum(1 for token in tokens if token in self.positive_words)
        negative_count = sum(1 for token in tokens if token in self.negative_words)
        
        # Calculate score
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            score = 0.0
            polarity = SentimentPolarity.NEUTRAL
            confidence = 0.3  # Low confidence for neutral
        else:
            # Score from -1.0 (negative) to +1.0 (positive)
            score = (positive_count - negative_count) / total_sentiment_words
            
            # Determine polarity
            if score > 0.1:
                polarity = SentimentPolarity.POSITIVE
            elif score < -0.1:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.NEUTRAL
            
            # Confidence based on number of sentiment words
            confidence = min(1.0, total_sentiment_words / 10)
        
        # Estimate subjectivity (ratio of sentiment words to total words)
        subjectivity = min(1.0, total_sentiment_words / max(1, len(tokens)))
        
        return SentimentResult(
            score=score,
            polarity=polarity,
            confidence=confidence,
            subjectivity=subjectivity,
        )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment of multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of SentimentResults
        """
        return [self.analyze(text) for text in texts]
    
    def get_sentiment_summary(self, text: str) -> Dict[str, any]:
        """
        Get sentiment summary (convenience method).
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment info
        """
        result = self.analyze(text)
        
        return {
            'sentiment': result.polarity.value,
            'score': result.score,
            'confidence': result.confidence,
            'subjectivity': result.subjectivity,
        }


# Export
__all__ = [
    'SentimentAnalyzer',
    'SentimentResult',
    'SentimentPolarity',
]
