"""
apps/vigil-platform/ai/article_processor.py

Article processing using shared_ai components.

Integrates:
- NLP preprocessing (shared_ai.nlp)
- Named entity recognition
- Sentiment analysis
- Embeddings (shared_ai.embeddings)
- Topic modeling (shared_ai.topics)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from shared_types import ScrapedArticle
from shared_ai.nlp import (
    TextPreprocessor,
    NamedEntityRecognizer,
    SentimentAnalyzer,
    SPACY_AVAILABLE,
)
from shared_ai.embeddings import (
    TextEmbedder,
    SENTENCE_TRANSFORMERS_AVAILABLE,
)


@dataclass
class ProcessedArticle:
    """
    Article after AI processing.
    
    Attributes:
        article: Original scraped article
        tokens: Preprocessed tokens
        entities: Named entities
        sentiment: Sentiment analysis result
        embedding: Article embedding vector
        topic: Assigned topic (if available)
    """
    article: ScrapedArticle
    tokens: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    sentiment: Optional[Dict] = None
    embedding: Optional[any] = None
    topic: Optional[int] = None
    topic_words: List[tuple] = field(default_factory=list)


class VigilArticleProcessor:
    """
    Complete article processing pipeline for Vigil.
    
    Uses shared_ai components:
    - Text preprocessing
    - Named entity recognition
    - Sentiment analysis
    - Embeddings
    
    Usage:
        processor = VigilArticleProcessor(
            enable_nlp=True,
            enable_embeddings=True,
        )
        
        # Process single article
        processed = processor.process_article(article)
        
        # Access results
        print(processed.tokens)
        print(processed.entities)
        print(processed.sentiment)
    """
    
    def __init__(
        self,
        enable_nlp: bool = True,
        enable_embeddings: bool = True,
        embedding_model: str = "sentence-camembert-base",
    ):
        """
        Initialize processor.
        
        Args:
            enable_nlp: Enable NLP processing (requires spaCy)
            enable_embeddings: Enable embeddings (requires sentence-transformers)
            embedding_model: Embedding model name
        """
        self.enable_nlp = enable_nlp
        self.enable_embeddings = enable_embeddings
        
        # Initialize NLP components
        if enable_nlp:
            if not SPACY_AVAILABLE:
                raise ImportError(
                    "spaCy is required for NLP processing. "
                    "Install with: pip install spacy && python -m spacy download fr_core_news_md"
                )
            
            self.preprocessor = TextPreprocessor(language="fr")
            self.ner = NamedEntityRecognizer(language="fr")
        else:
            self.preprocessor = None
            self.ner = None
        
        # Sentiment analyzer (always available, no dependencies)
        self.sentiment_analyzer = SentimentAnalyzer(language="fr")
        
        # Initialize embeddings
        if enable_embeddings:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
            
            self.embedder = TextEmbedder(model_name=embedding_model)
        else:
            self.embedder = None
    
    def process_article(self, article: ScrapedArticle) -> ProcessedArticle:
        """
        Process article through complete pipeline.
        
        Args:
            article: Scraped article
            
        Returns:
            ProcessedArticle with all analysis
        """
        processed = ProcessedArticle(article=article)
        
        # Get text to process
        text = self._get_text_for_processing(article)
        
        if not text:
            return processed
        
        # 1. NLP preprocessing
        if self.preprocessor:
            try:
                result = self.preprocessor.process(text)
                processed.tokens = result.filtered_tokens
            except Exception as e:
                print(f"NLP preprocessing error: {e}")
        
        # 2. Named entity recognition
        if self.ner:
            try:
                entities = self.ner.extract_political_entities(text)
                processed.entities = entities
            except Exception as e:
                print(f"NER error: {e}")
        
        # 3. Sentiment analysis
        try:
            sentiment = self.sentiment_analyzer.get_sentiment_summary(text)
            processed.sentiment = sentiment
        except Exception as e:
            print(f"Sentiment error: {e}")
        
        # 4. Embeddings
        if self.embedder:
            try:
                embedding = self.embedder.embed(text)
                processed.embedding = embedding
            except Exception as e:
                print(f"Embedding error: {e}")
        
        return processed
    
    def process_batch(
        self,
        articles: List[ScrapedArticle],
        show_progress: bool = True,
    ) -> List[ProcessedArticle]:
        """
        Process batch of articles efficiently.
        
        Args:
            articles: List of articles
            show_progress: Show progress bar
            
        Returns:
            List of ProcessedArticle
        """
        results = []
        
        # Process each article
        for i, article in enumerate(articles):
            if show_progress and i % 10 == 0:
                print(f"Processing {i}/{len(articles)}...")
            
            processed = self.process_article(article)
            results.append(processed)
        
        return results
    
    def _get_text_for_processing(self, article: ScrapedArticle) -> str:
        """
        Extract text from article for processing.
        
        Prioritizes: body_text > title
        
        Args:
            article: Scraped article
            
        Returns:
            Text for processing
        """
        if article.body_text:
            return article.body_text
        elif article.title:
            return article.title
        else:
            return ""
    
    def get_article_summary(self, processed: ProcessedArticle) -> Dict:
        """
        Get summary of processed article.
        
        Args:
            processed: ProcessedArticle
            
        Returns:
            Summary dictionary
        """
        return {
            'article_id': processed.article.article_id,
            'title': processed.article.title,
            'source': processed.article.source_name,
            'num_tokens': len(processed.tokens),
            'num_entities': sum(len(v) for v in processed.entities.values()),
            'people': processed.entities.get('people', []),
            'organizations': processed.entities.get('organizations', []),
            'sentiment': processed.sentiment.get('sentiment') if processed.sentiment else None,
            'has_embedding': processed.embedding is not None,
            'topic': processed.topic,
        }


# Export
__all__ = [
    'VigilArticleProcessor',
    'ProcessedArticle',
]
