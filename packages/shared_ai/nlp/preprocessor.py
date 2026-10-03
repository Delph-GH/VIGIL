"""
shared_ai/nlp/preprocessor.py

Text preprocessing using spaCy for French political content.

Extracted from Vigil's processing/nlp/preprocessor.py

Features:
- Text cleaning and normalization
- Tokenization with spaCy
- Lemmatization
- Stop word removal
- Language detection
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass

# Note: spaCy is an optional dependency
# Users must install: pip install spacy
# And download model: python -m spacy download fr_core_news_md

try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None
    Language = None


@dataclass
class ProcessedText:
    """
    Result of text preprocessing.
    
    Attributes:
        original: Original text
        cleaned: Cleaned text
        tokens: List of tokens
        lemmas: List of lemmatized tokens
        filtered_tokens: Tokens after stop word removal
        language: Detected language code
    """
    original: str
    cleaned: str
    tokens: List[str]
    lemmas: List[str]
    filtered_tokens: List[str]
    language: Optional[str] = None


class TextPreprocessor:
    """
    Text preprocessing for French political content.
    
    Uses spaCy for:
    - Tokenization
    - Lemmatization
    - POS tagging
    - Stop word removal
    
    Usage:
        preprocessor = TextPreprocessor(language="fr")
        
        result = preprocessor.process(text)
        
        print(result.cleaned)
        print(result.tokens)
        print(result.lemmas)
    """
    
    def __init__(
        self,
        language: str = "fr",
        model_name: Optional[str] = None,
        remove_stopwords: bool = True,
        lowercase: bool = True,
    ):
        """
        Initialize preprocessor.
        
        Args:
            language: Language code (fr, en, de)
            model_name: spaCy model name (default: fr_core_news_md)
            remove_stopwords: Remove stop words
            lowercase: Convert to lowercase
        """
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy is required for NLP preprocessing. "
                "Install with: pip install spacy && python -m spacy download fr_core_news_md"
            )
        
        self.language = language
        self.remove_stopwords = remove_stopwords
        self.lowercase = lowercase
        
        # Load spaCy model
        if model_name is None:
            model_name = self._get_default_model(language)
        
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise ValueError(
                f"spaCy model '{model_name}' not found. "
                f"Download with: python -m spacy download {model_name}"
            )
    
    def _get_default_model(self, language: str) -> str:
        """Get default spaCy model for language."""
        models = {
            'fr': 'fr_core_news_md',
            'en': 'en_core_web_md',
            'de': 'de_core_news_md',
        }
        return models.get(language, 'fr_core_news_md')
    
    def clean_text(self, text: str) -> str:
        """
        Clean text (basic normalization).
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters (keep French accents)
        text = re.sub(r'[^\w\s\-àâäéèêëïîôùûüÿæœçÀÂÄÉÈÊËÏÎÔÙÛÜŸÆŒÇ]', ' ', text)
        
        # Remove extra whitespace again
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Lowercase if configured
        if self.lowercase:
            text = text.lower()
        
        return text
    
    def process(self, text: str) -> ProcessedText:
        """
        Process text through complete pipeline.
        
        Args:
            text: Raw text
            
        Returns:
            ProcessedText with tokens, lemmas, etc.
        """
        if not text:
            return ProcessedText(
                original=text,
                cleaned="",
                tokens=[],
                lemmas=[],
                filtered_tokens=[],
                language=self.language,
            )
        
        # Clean text
        cleaned = self.clean_text(text)
        
        # Process with spaCy
        doc = self.nlp(cleaned)
        
        # Extract tokens
        tokens = [token.text for token in doc]
        
        # Extract lemmas
        lemmas = [token.lemma_ for token in doc]
        
        # Filter tokens (remove stop words and punctuation)
        if self.remove_stopwords:
            filtered_tokens = [
                token.lemma_
                for token in doc
                if not token.is_stop and not token.is_punct and token.text.strip()
            ]
        else:
            filtered_tokens = [
                token.lemma_
                for token in doc
                if not token.is_punct and token.text.strip()
            ]
        
        return ProcessedText(
            original=text,
            cleaned=cleaned,
            tokens=tokens,
            lemmas=lemmas,
            filtered_tokens=filtered_tokens,
            language=self.language,
        )
    
    def batch_process(self, texts: List[str]) -> List[ProcessedText]:
        """
        Process multiple texts efficiently.
        
        Args:
            texts: List of raw texts
            
        Returns:
            List of ProcessedText results
        """
        results = []
        
        for text in texts:
            result = self.process(text)
            results.append(result)
        
        return results
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Raw text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        cleaned = self.clean_text(text)
        doc = self.nlp(cleaned)
        
        sentences = [sent.text.strip() for sent in doc.sents]
        
        return sentences


# Export
__all__ = [
    'TextPreprocessor',
    'ProcessedText',
    'SPACY_AVAILABLE',
]
