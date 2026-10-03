"""
shared_ai/topics/topic_evolution.py

Track topic evolution over time.

Extracted from Vigil's processing/topics/topic_evolution.py

Features:
- Temporal topic analysis
- Topic trends tracking
- Topic emergence detection
- Topic stability analysis
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np


class TopicEvolution:
    """
    Track how topics evolve over time.
    
    Analyzes:
    - Topic frequency over time periods
    - Emerging topics
    - Declining topics  
    - Topic stability
    
    Usage:
        evolution = TopicEvolution()
        
        # Add documents with timestamps
        for doc in documents:
            evolution.add_document(
                doc_id=doc['id'],
                topic_id=doc['topic'],
                timestamp=doc['timestamp'],
            )
        
        # Get trends
        trends = evolution.get_topic_trends(
            time_periods=["2024-01", "2024-02", "2024-03"],
        )
        
        # Find emerging topics
        emerging = evolution.find_emerging_topics(
            recent_period="2024-03",
            previous_period="2024-02",
        )
    """
    
    def __init__(self):
        """Initialize evolution tracker."""
        self.documents: List[Dict] = []
        self.topic_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    
    def add_document(
        self,
        doc_id: str,
        topic_id: int,
        timestamp: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Add document to tracker.
        
        Args:
            doc_id: Document identifier
            topic_id: Assigned topic
            timestamp: ISO timestamp or date string
            metadata: Optional metadata
        """
        # Parse timestamp to period (e.g., "2024-01")
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            period = dt.strftime("%Y-%m")
        except:
            # Fallback: use timestamp as-is
            period = timestamp[:7] if len(timestamp) >= 7 else timestamp
        
        # Store document
        doc = {
            'doc_id': doc_id,
            'topic_id': topic_id,
            'timestamp': timestamp,
            'period': period,
            'metadata': metadata or {},
        }
        
        self.documents.append(doc)
        
        # Update counts
        self.topic_counts[period][topic_id] += 1
    
    def add_documents_batch(
        self,
        documents: List[Dict],
    ):
        """
        Add multiple documents.
        
        Args:
            documents: List of dicts with doc_id, topic_id, timestamp
        """
        for doc in documents:
            self.add_document(
                doc_id=doc['doc_id'],
                topic_id=doc['topic_id'],
                timestamp=doc['timestamp'],
                metadata=doc.get('metadata'),
            )
    
    def get_topic_trends(
        self,
        time_periods: Optional[List[str]] = None,
    ) -> Dict[int, List[int]]:
        """
        Get topic frequency trends over time.
        
        Args:
            time_periods: List of time periods (e.g., ["2024-01", "2024-02"])
                         If None, uses all periods
            
        Returns:
            Dictionary mapping topic_id to list of counts per period
        """
        # Get all periods if not specified
        if time_periods is None:
            time_periods = sorted(self.topic_counts.keys())
        
        # Get all topics
        all_topics = set()
        for period_topics in self.topic_counts.values():
            all_topics.update(period_topics.keys())
        
        # Build trends
        trends = {}
        
        for topic_id in all_topics:
            counts = []
            for period in time_periods:
                count = self.topic_counts[period].get(topic_id, 0)
                counts.append(count)
            
            trends[topic_id] = counts
        
        return trends
    
    def find_emerging_topics(
        self,
        recent_period: str,
        previous_period: str,
        min_growth: float = 2.0,
        min_recent_count: int = 5,
    ) -> List[Dict]:
        """
        Find emerging topics.
        
        A topic is "emerging" if it has:
        - Significant growth from previous to recent period
        - Minimum count in recent period
        
        Args:
            recent_period: Recent time period
            previous_period: Previous time period
            min_growth: Minimum growth ratio (e.g., 2.0 = doubled)
            min_recent_count: Minimum count in recent period
            
        Returns:
            List of dicts with topic info
        """
        recent_counts = self.topic_counts[recent_period]
        previous_counts = self.topic_counts[previous_period]
        
        emerging = []
        
        for topic_id, recent_count in recent_counts.items():
            # Check minimum count
            if recent_count < min_recent_count:
                continue
            
            previous_count = previous_counts.get(topic_id, 0)
            
            # Calculate growth
            if previous_count == 0:
                # New topic
                growth = float('inf')
            else:
                growth = recent_count / previous_count
            
            # Check if emerging
            if growth >= min_growth:
                emerging.append({
                    'topic_id': topic_id,
                    'recent_count': recent_count,
                    'previous_count': previous_count,
                    'growth_ratio': growth,
                })
        
        # Sort by growth
        emerging.sort(key=lambda x: x['growth_ratio'], reverse=True)
        
        return emerging
    
    def find_declining_topics(
        self,
        recent_period: str,
        previous_period: str,
        max_decline: float = 0.5,
        min_previous_count: int = 10,
    ) -> List[Dict]:
        """
        Find declining topics.
        
        Args:
            recent_period: Recent time period
            previous_period: Previous time period
            max_decline: Maximum decline ratio (e.g., 0.5 = halved)
            min_previous_count: Minimum count in previous period
            
        Returns:
            List of dicts with topic info
        """
        recent_counts = self.topic_counts[recent_period]
        previous_counts = self.topic_counts[previous_period]
        
        declining = []
        
        for topic_id, previous_count in previous_counts.items():
            # Check minimum previous count
            if previous_count < min_previous_count:
                continue
            
            recent_count = recent_counts.get(topic_id, 0)
            
            # Calculate decline
            if previous_count > 0:
                decline_ratio = recent_count / previous_count
            else:
                decline_ratio = 1.0
            
            # Check if declining
            if decline_ratio <= max_decline:
                declining.append({
                    'topic_id': topic_id,
                    'recent_count': recent_count,
                    'previous_count': previous_count,
                    'decline_ratio': decline_ratio,
                })
        
        # Sort by decline
        declining.sort(key=lambda x: x['decline_ratio'])
        
        return declining
    
    def get_topic_stability(
        self,
        topic_id: int,
        time_periods: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate topic stability (coefficient of variation).
        
        Lower values = more stable
        Higher values = more variable
        
        Args:
            topic_id: Topic ID
            time_periods: Time periods to analyze
            
        Returns:
            Stability score (coefficient of variation)
        """
        if time_periods is None:
            time_periods = sorted(self.topic_counts.keys())
        
        # Get counts
        counts = []
        for period in time_periods:
            count = self.topic_counts[period].get(topic_id, 0)
            counts.append(count)
        
        if not counts or all(c == 0 for c in counts):
            return 0.0
        
        # Calculate coefficient of variation (std / mean)
        mean = np.mean(counts)
        std = np.std(counts)
        
        if mean == 0:
            return 0.0
        
        cv = std / mean
        
        return float(cv)
    
    def get_period_summary(
        self,
        period: str,
        top_n: int = 10,
    ) -> Dict:
        """
        Get summary for a time period.
        
        Args:
            period: Time period
            top_n: Number of top topics
            
        Returns:
            Summary dict
        """
        counts = self.topic_counts[period]
        
        # Sort by count
        sorted_topics = sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        top_topics = sorted_topics[:top_n]
        
        return {
            'period': period,
            'total_documents': sum(counts.values()),
            'unique_topics': len(counts),
            'top_topics': [
                {'topic_id': topic_id, 'count': count}
                for topic_id, count in top_topics
            ],
        }
    
    def clear(self):
        """Clear all data."""
        self.documents.clear()
        self.topic_counts.clear()


# Export
__all__ = [
    'TopicEvolution',
]
