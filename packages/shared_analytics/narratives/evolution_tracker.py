"""
shared_analytics/narratives/evolution_tracker.py

Track narrative evolution over time.

Monitors how narratives grow, decline, merge, or split.
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import math

from .detector import Narrative


class NarrativeEvolution:
    """
    Track narrative changes over time.
    
    Monitors:
    - Growth/decline patterns
    - Narrative mutations
    - Convergence/divergence
    - Lifecycle stages
    """
    
    def __init__(self):
        """Initialize tracker."""
        # Store narrative snapshots over time
        self._snapshots = defaultdict(list)  # {period: [narratives]}
        self._narrative_history = {}  # {narrative_id: [periods]}
    
    def add_snapshot(
        self,
        period: str,
        narratives: List[Narrative],
    ):
        """
        Add narrative snapshot for time period.
        
        Args:
            period: Time period (e.g., "2024-05", "week_20")
            narratives: Detected narratives
        """
        self._snapshots[period] = narratives
        
        # Update history
        for narrative in narratives:
            if narrative.narrative_id not in self._narrative_history:
                self._narrative_history[narrative.narrative_id] = []
            
            self._narrative_history[narrative.narrative_id].append(period)
    
    def get_growth_trends(
        self,
        narrative_id: str,
    ) -> Dict:
        """
        Get growth trend for narrative.
        
        Args:
            narrative_id: Narrative ID
            
        Returns:
            Dict with growth metrics
        """
        periods = self._narrative_history.get(narrative_id, [])
        
        if not periods:
            return {
                'periods': 0,
                'trend': 'unknown',
                'first_seen': None,
                'last_seen': None,
            }
        
        # Get article counts over time
        article_counts = []
        
        for period in sorted(periods):
            narratives = self._snapshots[period]
            
            for narrative in narratives:
                if narrative.narrative_id == narrative_id:
                    article_counts.append(len(narrative.article_ids))
                    break
        
        # Determine trend
        if len(article_counts) < 2:
            trend = 'stable'
        elif article_counts[-1] > article_counts[0] * 1.5:
            trend = 'growing'
        elif article_counts[-1] < article_counts[0] * 0.67:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'periods': len(periods),
            'trend': trend,
            'article_counts': article_counts,
            'first_seen': periods[0],
            'last_seen': periods[-1],
        }
    
    def find_emerging_narratives(
        self,
        recent_period: str,
        min_strength: float = 0.3,
    ) -> List[Dict]:
        """
        Find recently emerged narratives.
        
        Args:
            recent_period: Recent time period
            min_strength: Minimum strength threshold
            
        Returns:
            List of emerging narratives
        """
        recent_narratives = self._snapshots.get(recent_period, [])
        
        emerging = []
        
        for narrative in recent_narratives:
            # Check if new (first appearance in recent period)
            history = self._narrative_history.get(narrative.narrative_id, [])
            
            if len(history) <= 2 and narrative.strength >= min_strength:
                emerging.append({
                    'narrative_id': narrative.narrative_id,
                    'theme': narrative.theme,
                    'strength': narrative.strength,
                    'keywords': narrative.keywords,
                    'article_count': len(narrative.article_ids),
                    'first_seen': history[0] if history else recent_period,
                })
        
        # Sort by strength
        emerging.sort(key=lambda n: n['strength'], reverse=True)
        
        return emerging
    
    def find_declining_narratives(
        self,
        recent_period: str,
        decline_threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Find declining narratives.
        
        Args:
            recent_period: Recent time period
            decline_threshold: Decline ratio threshold
            
        Returns:
            List of declining narratives
        """
        recent_narratives = self._snapshots.get(recent_period, [])
        
        declining = []
        
        for narrative in recent_narratives:
            history = self._narrative_history.get(narrative.narrative_id, [])
            
            if len(history) < 2:
                continue
            
            # Get article counts
            current_count = len(narrative.article_ids)
            
            # Get previous count
            prev_period = history[-2]
            prev_narratives = self._snapshots[prev_period]
            
            prev_count = 0
            for prev_narrative in prev_narratives:
                if prev_narrative.narrative_id == narrative.narrative_id:
                    prev_count = len(prev_narrative.article_ids)
                    break
            
            # Check decline
            if prev_count > 0:
                decline_ratio = current_count / prev_count
                
                if decline_ratio < decline_threshold:
                    declining.append({
                        'narrative_id': narrative.narrative_id,
                        'theme': narrative.theme,
                        'decline_ratio': decline_ratio,
                        'current_count': current_count,
                        'previous_count': prev_count,
                    })
        
        return declining
    
    def detect_mutations(
        self,
        narrative_id: str,
        keyword_threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Detect narrative mutations (keyword changes).
        
        Args:
            narrative_id: Narrative ID
            keyword_threshold: Minimum overlap for non-mutation
            
        Returns:
            List of detected mutations
        """
        periods = self._narrative_history.get(narrative_id, [])
        
        if len(periods) < 2:
            return []
        
        mutations = []
        
        # Compare keywords across periods
        for i in range(1, len(periods)):
            prev_period = periods[i-1]
            curr_period = periods[i]
            
            prev_narrative = None
            curr_narrative = None
            
            # Get narratives
            for narrative in self._snapshots[prev_period]:
                if narrative.narrative_id == narrative_id:
                    prev_narrative = narrative
                    break
            
            for narrative in self._snapshots[curr_period]:
                if narrative.narrative_id == narrative_id:
                    curr_narrative = narrative
                    break
            
            if not prev_narrative or not curr_narrative:
                continue
            
            # Calculate keyword overlap
            prev_kw = set(prev_narrative.keywords)
            curr_kw = set(curr_narrative.keywords)
            
            overlap = len(prev_kw & curr_kw) / max(len(prev_kw), len(curr_kw))
            
            if overlap < keyword_threshold:
                mutations.append({
                    'from_period': prev_period,
                    'to_period': curr_period,
                    'keyword_overlap': overlap,
                    'new_keywords': list(curr_kw - prev_kw),
                    'dropped_keywords': list(prev_kw - curr_kw),
                })
        
        return mutations


# Export
__all__ = [
    'NarrativeEvolution',
]
