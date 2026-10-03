"""
apps/vigil-platform/search/article_search.py

Article similarity search for Vigil using shared_search.

Replaces old processing/embeddings/similarity_index.py with shared components.
"""

from typing import List, Dict, Optional
from pathlib import Path

from shared_types import ScrapedArticle
from shared_ai.embeddings import TextEmbedder
from shared_search import SimilaritySearch, FAISS_AVAILABLE


class VigilArticleSearch:
    """
    Article similarity search for Vigil political content.
    
    Uses shared_search.SimilaritySearch with FAISS backend.
    
    Features:
    - Build index from article corpus
    - Find similar political articles
    - Incremental updates
    - Index persistence
    
    Usage:
        # Initialize
        search = VigilArticleSearch(
            embedder=embedder,
            index_path="data/vigil_articles.idx",
        )
        
        # Build index
        search.build_index(articles)
        
        # Search
        results = search.find_similar(article, top_k=5)
        
        # Save
        search.save()
    """
    
    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        index_path: Optional[str] = None,
        embedding_model: str = "sentence-camembert-base",
    ):
        """
        Initialize article search.
        
        Args:
            embedder: TextEmbedder instance (creates if None)
            index_path: Path for index persistence
            embedding_model: Model name for embeddings
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required for article search")
        
        # Initialize embedder
        if embedder is None:
            embedder = TextEmbedder(model_name=embedding_model)
        
        self.embedder = embedder
        self.index_path = index_path
        
        # Initialize or load search index
        if index_path and Path(index_path).exists():
            self.search = SimilaritySearch.load(index_path, embedder)
        else:
            self.search = SimilaritySearch(
                embedder=embedder,
                dimension=embedder.embedding_dim,
            )
    
    def build_index(
        self,
        articles: List[ScrapedArticle],
        show_progress: bool = True,
    ):
        """
        Build search index from articles.
        
        Args:
            articles: List of articles
            show_progress: Show progress
        """
        # Extract texts and IDs
        texts = []
        doc_ids = []
        
        for article in articles:
            text = self._get_article_text(article)
            if text:
                texts.append(text)
                doc_ids.append(article.article_id)
        
        # Build index
        if show_progress:
            print(f"Building index from {len(texts)} articles...")
        
        self.search.build_index(
            documents=texts,
            doc_ids=doc_ids,
            show_progress=show_progress,
        )
        
        if show_progress:
            print(f"Index built: {self.search.size()} articles indexed")
    
    def find_similar(
        self,
        article: ScrapedArticle,
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> List[Dict]:
        """
        Find similar articles.
        
        Args:
            article: Query article
            top_k: Number of results
            exclude_self: Exclude query article from results
            
        Returns:
            List of similar article dicts with id, score
        """
        # Get article text
        text = self._get_article_text(article)
        
        if not text:
            return []
        
        # Search
        results = self.search.search(
            query=text,
            top_k=top_k + (1 if exclude_self else 0),
            return_texts=False,
        )
        
        # Filter out self if requested
        if exclude_self:
            results = [r for r in results if r['id'] != article.article_id][:top_k]
        
        return results
    
    def find_similar_by_text(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Find similar articles by text query.
        
        Args:
            query_text: Query text
            top_k: Number of results
            
        Returns:
            List of results
        """
        return self.search.search(
            query=query_text,
            top_k=top_k,
            return_texts=False,
        )
    
    def add_articles(
        self,
        articles: List[ScrapedArticle],
    ):
        """
        Add articles to existing index.
        
        Args:
            articles: Articles to add
        """
        texts = []
        doc_ids = []
        
        for article in articles:
            text = self._get_article_text(article)
            if text:
                texts.append(text)
                doc_ids.append(article.article_id)
        
        if texts:
            self.search.add_documents(texts, doc_ids)
    
    def save(self):
        """Save index to disk."""
        if self.index_path:
            self.search.save(self.index_path)
    
    def _get_article_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
        # Combine title and body
        parts = []
        
        if article.title:
            parts.append(article.title)
        
        if article.body_text:
            parts.append(article.body_text)
        
        return " ".join(parts)
    
    def size(self) -> int:
        """Get number of indexed articles."""
        return self.search.size()


# Export
__all__ = [
    'VigilArticleSearch',
]
