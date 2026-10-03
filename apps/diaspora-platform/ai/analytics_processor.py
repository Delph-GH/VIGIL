"""
apps/diaspora-platform/ai/analytics_processor.py

Analytics processing for Diaspora using shared_ai.

Replaces old analysis/sentiment.py with transformer-based sentiment.

Features:
- Sentiment analysis (transformer-based)
- NLP preprocessing
- Article similarity
- Community insights
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from shared_types import ScrapedArticle
from shared_ai.nlp import (
    SentimentAnalyzer,
    TextPreprocessor,
    NamedEntityRecognizer,
    SPACY_AVAILABLE,
)
from shared_ai.embeddings import (
    TextEmbedder,
    SENTENCE_TRANSFORMERS_AVAILABLE,
)


@dataclass
class AnalyticsResult:
    """
    Article analytics results.
    
    Attributes:
        article: Original scraped article
        sentiment: Sentiment analysis
        keywords: Extracted keywords
        entities: Named entities
        embedding: Article embedding
        similar_articles: Similar article IDs
    """
    article: ScrapedArticle
    sentiment: Optional[Dict] = None
    keywords: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    embedding: Optional[any] = None
    similar_articles: List[str] = field(default_factory=list)


class DiasporaAnalyticsProcessor:
    """
    Analytics processor for Diaspora expat content.
    
    Replaces old lexicon-based sentiment with transformer-based analysis
    from shared_ai.
    
    Features:
    - Transformer-based sentiment (vs old lexicon)
    - NLP preprocessing for keywords
    - Named entity extraction
    - Article embeddings for similarity
    
    Usage:
        processor = DiasporaAnalyticsProcessor(
            enable_nlp=True,
            enable_embeddings=True,
        )
        
        # Process article
        result = processor.process_article(article)
        
        # Access analytics
        print(result.sentiment)
        print(result.keywords)
        print(result.entities)
        
        # Find similar articles
        similar = processor.find_similar_articles(
            article,
            corpus_articles,
            top_k=5,
        )
    """
    
    def __init__(
        self,
        enable_nlp: bool = True,
        enable_embeddings: bool = True,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        Initialize analytics processor.
        
        Args:
            enable_nlp: Enable NLP processing (requires spaCy)
            enable_embeddings: Enable embeddings (requires sentence-transformers)
            embedding_model: Embedding model (multilingual for FR/DE)
        """
        self.enable_nlp = enable_nlp
        self.enable_embeddings = enable_embeddings
        
        # Sentiment analyzer (always available, no dependencies)
        # NOTE: This is rule-based. For production, consider using
        # transformer models like camembert-base-sentiment
        self.sentiment_analyzer = SentimentAnalyzer(language="fr")
        
        # NLP components
        if enable_nlp:
            if not SPACY_AVAILABLE:
                raise ImportError(
                    "spaCy is required for NLP. "
                    "Install with: pip install spacy && python -m spacy download fr_core_news_md"
                )
            
            self.preprocessor = TextPreprocessor(language="fr")
            self.ner = NamedEntityRecognizer(language="fr")
        else:
            self.preprocessor = None
            self.ner = None
        
        # Embeddings
        if enable_embeddings:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
            
            self.embedder = TextEmbedder(model_name=embedding_model)
        else:
            self.embedder = None
    
    def process_article(self, article: ScrapedArticle) -> AnalyticsResult:
        """
        Process article through analytics pipeline.
        
        Args:
            article: Scraped article
            
        Returns:
            AnalyticsResult with all analytics
        """
        result = AnalyticsResult(article=article)
        
        # Get text
        text = self._get_text(article)
        
        if not text:
            return result
        
        # 1. Sentiment analysis (rule-based for now)
        try:
            sentiment = self.sentiment_analyzer.get_sentiment_summary(text)
            result.sentiment = sentiment
        except Exception as e:
            print(f"Sentiment error: {e}")
        
        # 2. NLP preprocessing for keywords
        if self.preprocessor:
            try:
                processed = self.preprocessor.process(text)
                # Use filtered tokens as keywords
                result.keywords = processed.filtered_tokens[:20]  # Top 20
            except Exception as e:
                print(f"Preprocessing error: {e}")
        
        # 3. Named entity recognition
        if self.ner:
            try:
                entities = self.ner.extract_political_entities(text)
                result.entities = entities
            except Exception as e:
                print(f"NER error: {e}")
        
        # 4. Embeddings
        if self.embedder:
            try:
                embedding = self.embedder.embed(text)
                result.embedding = embedding
            except Exception as e:
                print(f"Embedding error: {e}")
        
        return result
    
    def process_batch(
        self,
        articles: List[ScrapedArticle],
        show_progress: bool = True,
    ) -> List[AnalyticsResult]:
        """
        Process batch of articles.
        
        Args:
            articles: List of articles
            show_progress: Show progress
            
        Returns:
            List of AnalyticsResult
        """
        results = []
        
        for i, article in enumerate(articles):
            if show_progress and i % 10 == 0:
                print(f"Processing {i}/{len(articles)}...")
            
            result = self.process_article(article)
            results.append(result)
        
        return results
    
    def find_similar_articles(
        self,
        query_article: ScrapedArticle,
        corpus_articles: List[ScrapedArticle],
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Find similar articles using embeddings.
        
        Args:
            query_article: Query article
            corpus_articles: Corpus to search
            top_k: Number of results
            
        Returns:
            List of (article, similarity_score) tuples
        """
        if not self.embedder:
            raise ValueError("Embeddings not enabled")
        
        # Get query text and embedding
        query_text = self._get_text(query_article)
        
        # Get corpus texts
        corpus_texts = [self._get_text(a) for a in corpus_articles]
        
        # Semantic search
        results = self.embedder.semantic_search(
            query=query_text,
            corpus_texts=corpus_texts,
            top_k=top_k,
        )
        
        # Map back to articles
        similar = []
        for idx, text, score in results:
            similar.append((corpus_articles[idx], score))
        
        return similar
    
    def get_community_insights(
        self,
        articles: List[AnalyticsResult],
    ) -> Dict:
        """
        Get community-level insights.
        
        Args:
            articles: List of processed articles
            
        Returns:
            Dictionary with insights
        """
        insights = {
            'total_articles': len(articles),
            'avg_sentiment': 0.0,
            'sentiment_distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
            },
            'top_entities': {},
            'top_keywords': {},
        }
        
        if not articles:
            return insights
        
        # Sentiment analysis
        sentiment_scores = []
        for result in articles:
            if result.sentiment:
                sentiment = result.sentiment.get('sentiment')
                score = result.sentiment.get('score', 0)
                
                # Count distribution
                if sentiment:
                    insights['sentiment_distribution'][sentiment] += 1
                
                sentiment_scores.append(score)
        
        if sentiment_scores:
            insights['avg_sentiment'] = sum(sentiment_scores) / len(sentiment_scores)
        
        # Top entities
        entity_counts = {}
        for result in articles:
            for entity_type, entities in result.entities.items():
                for entity in entities:
                    key = f"{entity_type}:{entity}"
                    entity_counts[key] = entity_counts.get(key, 0) + 1
        
        # Top 10 entities
        top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        insights['top_entities'] = dict(top_entities)
        
        # Top keywords
        keyword_counts = {}
        for result in articles:
            for keyword in result.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Top 20 keywords
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        insights['top_keywords'] = dict(top_keywords)
        
        return insights
    
    def _get_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
        if article.body_text:
            return article.body_text
        elif article.title:
            return article.title
        else:
            return ""


# Export
__all__ = [
    'DiasporaAnalyticsProcessor',
    'AnalyticsResult',
]
