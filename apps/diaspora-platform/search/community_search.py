"""
apps/diaspora-platform/search/community_search.py

Community article search for Diaspora using shared_search.

New capability: FAISS-based similarity search for expat community content.
"""

from typing import List, Dict, Optional
from pathlib import Path

from shared_types import ScrapedArticle
from shared_ai.embeddings import TextEmbedder
from shared_search import SimilaritySearch, FAISS_AVAILABLE


class DiasporaCommunitySearch:
    """
    Community article search for Diaspora expat content.
    
    Uses shared_search.SimilaritySearch with FAISS backend.
    
    Features:
    - Find similar community articles
    - Multilingual support (FR, DE, EN)
    - Location-based filtering
    - Index persistence
    
    Usage:
        # Initialize
        search = DiasporaCommunitySearch(
            embedder=embedder,
            index_path="data/diaspora_articles.idx",
        )
        
        # Build index
        search.build_index(articles)
        
        # Find similar
        results = search.find_similar(article, top_k=5)
        
        # Search by topic
        results = search.search_by_topic("community events", top_k=10)
    """
    
    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        index_path: Optional[str] = None,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        Initialize community search.
        
        Args:
            embedder: TextEmbedder instance
            index_path: Path for index persistence
            embedding_model: Model name (multilingual for FR/DE/EN)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required for community search")
        
        # Initialize embedder (use multilingual model)
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
        
        # Store article metadata
        self._article_metadata = {}  # id -> metadata
    
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
        texts = []
        doc_ids = []
        
        for article in articles:
            text = self._get_article_text(article)
            if text:
                texts.append(text)
                doc_ids.append(article.article_id)
                
                # Store metadata
                self._article_metadata[article.article_id] = {
                    'title': article.title,
                    'source': article.source_name,
                    'url': article.url,
                }
        
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
        Find similar community articles.
        
        Args:
            article: Query article
            top_k: Number of results
            exclude_self: Exclude query article
            
        Returns:
            List of similar articles with metadata
        """
        text = self._get_article_text(article)
        
        if not text:
            return []
        
        # Search
        results = self.search.search(
            query=text,
            top_k=top_k + (1 if exclude_self else 0),
            return_texts=False,
        )
        
        # Filter self
        if exclude_self:
            results = [r for r in results if r['id'] != article.article_id][:top_k]
        
        # Add metadata
        for result in results:
            metadata = self._article_metadata.get(result['id'], {})
            result.update(metadata)
        
        return results
    
    def search_by_topic(
        self,
        topic_query: str,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Search articles by topic/keyword.
        
        Args:
            topic_query: Topic or keyword query
            top_k: Number of results
            
        Returns:
            List of matching articles
        """
        results = self.search.search(
            query=topic_query,
            top_k=top_k,
            return_texts=False,
        )
        
        # Add metadata
        for result in results:
            metadata = self._article_metadata.get(result['id'], {})
            result.update(metadata)
        
        return results
    
    def search_by_location(
        self,
        location: str,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Search articles by location (city, country).
        
        Args:
            location: Location query (e.g., "Munich", "Bavaria")
            top_k: Number of results
            
        Returns:
            List of location-relevant articles
        """
        return self.search_by_topic(f"{location} community", top_k=top_k)
    
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
                
                # Store metadata
                self._article_metadata[article.article_id] = {
                    'title': article.title,
                    'source': article.source_name,
                    'url': article.url,
                }
        
        if texts:
            self.search.add_documents(texts, doc_ids)
    
    def save(self):
        """Save index and metadata."""
        if self.index_path:
            import json
            
            # Save search index
            self.search.save(self.index_path)
            
            # Save metadata
            metadata_path = Path(self.index_path).with_suffix('.metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(self._article_metadata, f)
    
    def load_metadata(self):
        """Load article metadata."""
        if self.index_path:
            import json
            
            metadata_path = Path(self.index_path).with_suffix('.metadata.json')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self._article_metadata = json.load(f)
    
    def _get_article_text(self, article: ScrapedArticle) -> str:
        """Extract text from article."""
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
    'DiasporaCommunitySearch',
]
