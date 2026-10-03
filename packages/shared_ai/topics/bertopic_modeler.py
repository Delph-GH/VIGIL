"""
shared_ai/topics/bertopic_modeler.py

Topic modeling using BERTopic for French political content.

Extracted from Vigil's processing/topics/bertopic_modeler.py

Features:
- Topic discovery from text corpora
- French-optimized topic extraction
- Topic representation
- Document-topic assignment
"""

from typing import List, Dict, Optional, Tuple
import numpy as np

# Optional dependencies
try:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    BERTopic = None
    UMAP = None
    HDBSCAN = None
    CountVectorizer = None


class TopicModeler:
    """
    Topic modeling using BERTopic with French optimization.
    
    BERTopic pipeline:
    1. Embed documents (using sentence-transformers)
    2. Reduce dimensionality (UMAP)
    3. Cluster documents (HDBSCAN)
    4. Extract topics (c-TF-IDF)
    
    Usage:
        from shared_ai.embeddings import TextEmbedder
        
        # Initialize with French embedder
        embedder = TextEmbedder(model_name="sentence-camembert-base")
        
        modeler = TopicModeler(
            embedder=embedder,
            language="french",
            min_topic_size=10,
        )
        
        # Fit on corpus
        topics, probs = modeler.fit_transform(documents)
        
        # Get topic info
        topic_info = modeler.get_topic_info()
        
        # Get topic words
        topic_words = modeler.get_topic_words(topic_id=0)
    """
    
    def __init__(
        self,
        embedder=None,
        language: str = "french",
        min_topic_size: int = 10,
        nr_topics: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialize topic modeler.
        
        Args:
            embedder: TextEmbedder instance (optional, uses default if None)
            language: Language for stopwords
            min_topic_size: Minimum topic size
            nr_topics: Number of topics (None = auto)
            verbose: Verbose output
        """
        if not BERTOPIC_AVAILABLE:
            raise ImportError(
                "BERTopic and dependencies are required. "
                "Install with: pip install bertopic umap-learn hdbscan"
            )
        
        self.embedder = embedder
        self.language = language
        self.min_topic_size = min_topic_size
        self.nr_topics = nr_topics
        self.verbose = verbose
        
        # Initialize BERTopic model
        self.model = self._create_model()
        
        # Topic info cache
        self._topics = None
        self._topic_info = None
    
    def _create_model(self) -> BERTopic:
        """Create BERTopic model with custom parameters."""
        
        # UMAP for dimensionality reduction
        umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric='cosine',
            random_state=42,
        )
        
        # HDBSCAN for clustering
        hdbscan_model = HDBSCAN(
            min_cluster_size=self.min_topic_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True,
        )
        
        # CountVectorizer for topic representation
        # French stopwords
        stop_words = self._get_stopwords()
        
        vectorizer_model = CountVectorizer(
            ngram_range=(1, 2),
            stop_words=stop_words,
            min_df=2,
        )
        
        # Create BERTopic model
        model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            nr_topics=self.nr_topics,
            verbose=self.verbose,
            calculate_probabilities=True,
        )
        
        return model
    
    def _get_stopwords(self) -> List[str]:
        """Get French stopwords."""
        # Basic French stopwords
        # In production, use a comprehensive stopwords list
        french_stopwords = [
            'le', 'la', 'les', 'un', 'une', 'des',
            'du', 'de', 'et', 'à', 'en', 'dans',
            'pour', 'par', 'sur', 'avec', 'sans',
            'ce', 'ces', 'cet', 'cette',
            'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
            'je', 'tu', 'me', 'te', 'se',
            'qui', 'que', 'quoi', 'dont', 'où',
            'est', 'sont', 'a', 'ont', 'été',
            'plus', 'moins', 'très', 'bien', 'mal',
        ]
        
        return french_stopwords
    
    def fit(self, documents: List[str]) -> 'TopicModeler':
        """
        Fit model on documents.
        
        Args:
            documents: List of text documents
            
        Returns:
            Self
        """
        if not documents:
            raise ValueError("Documents cannot be empty")
        
        # Get embeddings if embedder provided
        if self.embedder:
            embeddings = self.embedder.embed_batch(
                documents,
                show_progress=self.verbose,
            )
        else:
            embeddings = None
        
        # Fit BERTopic
        self.model.fit(documents, embeddings=embeddings)
        
        # Cache topics
        self._topics = self.model.topics_
        
        return self
    
    def transform(self, documents: List[str]) -> Tuple[List[int], np.ndarray]:
        """
        Transform documents to topics.
        
        Args:
            documents: List of text documents
            
        Returns:
            Tuple of (topics, probabilities)
        """
        if not documents:
            return [], np.array([])
        
        # Get embeddings if embedder provided
        if self.embedder:
            embeddings = self.embedder.embed_batch(
                documents,
                show_progress=False,
            )
        else:
            embeddings = None
        
        # Transform
        topics, probs = self.model.transform(documents, embeddings=embeddings)
        
        return topics, probs
    
    def fit_transform(
        self,
        documents: List[str],
    ) -> Tuple[List[int], np.ndarray]:
        """
        Fit and transform in one step.
        
        Args:
            documents: List of text documents
            
        Returns:
            Tuple of (topics, probabilities)
        """
        self.fit(documents)
        return self._topics, None  # BERTopic doesn't return probs in fit
    
    def get_topic_info(self) -> List[Dict]:
        """
        Get information about all topics.
        
        Returns:
            List of topic info dicts
        """
        if self.model.topics_ is None:
            return []
        
        # Get BERTopic topic info
        topic_info_df = self.model.get_topic_info()
        
        # Convert to list of dicts
        topic_info = []
        
        for _, row in topic_info_df.iterrows():
            topic_info.append({
                'topic': int(row['Topic']),
                'count': int(row['Count']),
                'name': row.get('Name', f"Topic {row['Topic']}"),
            })
        
        return topic_info
    
    def get_topic_words(
        self,
        topic_id: int,
        top_n: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Get top words for a topic.
        
        Args:
            topic_id: Topic ID
            top_n: Number of top words
            
        Returns:
            List of (word, score) tuples
        """
        topic = self.model.get_topic(topic_id)
        
        if topic is None or not topic:
            return []
        
        return topic[:top_n]
    
    def get_topic_labels(self) -> Dict[int, str]:
        """
        Get labels for all topics.
        
        Returns:
            Dictionary mapping topic_id to label
        """
        labels = {}
        
        for topic_id in set(self._topics or []):
            if topic_id == -1:  # Outlier topic
                labels[topic_id] = "Outliers"
            else:
                # Get top words
                words = self.get_topic_words(topic_id, top_n=3)
                if words:
                    label = "_".join([w[0] for w in words])
                    labels[topic_id] = label
                else:
                    labels[topic_id] = f"Topic_{topic_id}"
        
        return labels
    
    def reduce_topics(self, nr_topics: int):
        """
        Reduce number of topics.
        
        Args:
            nr_topics: Target number of topics
        """
        if self.model.topics_ is None:
            raise ValueError("Model must be fitted first")
        
        self.model.reduce_topics(
            docs=None,  # Uses cached documents
            nr_topics=nr_topics,
        )
        
        # Update cache
        self._topics = self.model.topics_
    
    def get_document_topics(
        self,
        documents: List[str],
    ) -> List[Dict]:
        """
        Get topics for documents.
        
        Args:
            documents: List of documents
            
        Returns:
            List of dicts with topic info per document
        """
        topics, probs = self.transform(documents)
        
        results = []
        
        for i, (topic_id, prob) in enumerate(zip(topics, probs)):
            if prob is not None:
                prob_value = float(prob[topic_id]) if len(prob) > 0 else 0.0
            else:
                prob_value = 0.0
            
            results.append({
                'document_id': i,
                'topic': topic_id,
                'probability': prob_value,
                'topic_words': self.get_topic_words(topic_id, top_n=5),
            })
        
        return results


# Export
__all__ = [
    'TopicModeler',
    'BERTOPIC_AVAILABLE',
]
