"""
shared_validation/human_validation.py

Human validation workflows and review queues.

Manages human-in-the-loop validation for articles
that require manual review.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

from shared_types import ScrapedArticle, ArticleStatus
from shared_utils import get_current_timestamp


class ValidationDecision(str, Enum):
    """
    Human validation decision.
    """
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ESCALATED = "escalated"
    PENDING = "pending"


@dataclass
class ValidationReview:
    """
    Human validation review record.
    
    Tracks who reviewed an article, when, and their decision.
    """
    article_id: str
    reviewer_id: str
    decision: ValidationDecision
    timestamp: str
    notes: Optional[str] = None
    confidence: Optional[float] = None  # 0-1
    tags: List[str] = field(default_factory=list)


class ValidationQueue:
    """
    Queue for articles awaiting human validation.
    
    Prioritizes articles based on:
    - Quality score (lower = higher priority)
    - Time in queue (older = higher priority)
    - Source importance
    
    Usage:
        queue = ValidationQueue()
        
        # Add article for review
        queue.add(article, quality_score=45.0, reason="Low quality score")
        
        # Get next article to review
        article, metadata = queue.get_next()
        
        # Submit review
        queue.submit_review(article_id, ValidationReview(...))
    """
    
    def __init__(self):
        """Initialize validation queue."""
        self._queue: Dict[str, 'QueuedArticle'] = {}
        self._reviews: Dict[str, List[ValidationReview]] = {}
    
    def add(
        self,
        article: ScrapedArticle,
        quality_score: float,
        reason: str,
        priority: Optional[int] = None,
    ) -> None:
        """
        Add article to validation queue.
        
        Args:
            article: Article to queue
            quality_score: Quality score (0-100)
            reason: Why article needs validation
            priority: Manual priority override (higher = more urgent)
        """
        queued = QueuedArticle(
            article=article,
            quality_score=quality_score,
            reason=reason,
            queued_at=get_current_timestamp(),
            priority=priority or self._calculate_priority(quality_score),
        )
        
        self._queue[article.article_id] = queued
    
    def get_next(self) -> Optional[tuple[ScrapedArticle, 'QueuedArticle']]:
        """
        Get next article for review (highest priority).
        
        Returns:
            Tuple of (article, metadata) or None if queue empty
        """
        if not self._queue:
            return None
        
        # Sort by priority (descending)
        sorted_items = sorted(
            self._queue.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        article_id, queued = sorted_items[0]
        return (queued.article, queued)
    
    def submit_review(
        self,
        article_id: str,
        review: ValidationReview,
        remove_from_queue: bool = True,
    ) -> None:
        """
        Submit validation review.
        
        Args:
            article_id: Article ID
            review: Validation review
            remove_from_queue: Remove from queue after review
        """
        # Store review
        if article_id not in self._reviews:
            self._reviews[article_id] = []
        
        self._reviews[article_id].append(review)
        
        # Remove from queue if approved/rejected
        if remove_from_queue and article_id in self._queue:
            if review.decision in [ValidationDecision.APPROVED, ValidationDecision.REJECTED]:
                del self._queue[article_id]
    
    def get_reviews(self, article_id: str) -> List[ValidationReview]:
        """Get all reviews for article."""
        return self._reviews.get(article_id, [])
    
    def get_queue_stats(self) -> Dict[str, any]:
        """Get queue statistics."""
        if not self._queue:
            return {
                'total': 0,
                'avg_priority': 0,
                'avg_quality_score': 0,
            }
        
        priorities = [q.priority for q in self._queue.values()]
        scores = [q.quality_score for q in self._queue.values()]
        
        return {
            'total': len(self._queue),
            'avg_priority': sum(priorities) / len(priorities),
            'avg_quality_score': sum(scores) / len(scores),
            'min_quality_score': min(scores),
            'max_quality_score': max(scores),
        }
    
    def _calculate_priority(self, quality_score: float) -> int:
        """
        Calculate priority based on quality score.
        
        Lower quality = higher priority (needs review sooner).
        
        Args:
            quality_score: Quality score (0-100)
            
        Returns:
            Priority (0-100)
        """
        # Invert score: lower quality = higher priority
        return int(100 - quality_score)


@dataclass
class QueuedArticle:
    """Article in validation queue with metadata."""
    article: ScrapedArticle
    quality_score: float
    reason: str
    queued_at: str
    priority: int
    reviewed_at: Optional[str] = None


class ValidationWorkflow:
    """
    Complete validation workflow manager.
    
    Combines automated + human validation:
    1. Automated checks (quality, hallucination)
    2. Human review (if needed)
    3. Final decision
    
    Usage:
        workflow = ValidationWorkflow()
        
        # Process article
        decision = workflow.process_article(article)
        
        if decision.needs_review:
            # Add to human review queue
            workflow.queue_for_review(article, decision.quality_score)
    """
    
    def __init__(
        self,
        quality_threshold: float = 70.0,
        auto_approve_threshold: float = 90.0,
    ):
        """
        Initialize workflow.
        
        Args:
            quality_threshold: Min score for approval (default: 70)
            auto_approve_threshold: Score for auto-approval (default: 90)
        """
        self.quality_threshold = quality_threshold
        self.auto_approve_threshold = auto_approve_threshold
        self.queue = ValidationQueue()
    
    def process_article(
        self,
        article: ScrapedArticle,
        quality_score: float,
        hallucination_issues: List[any],
    ) -> 'ValidationDecisionResult':
        """
        Process article through validation workflow.
        
        Args:
            article: Article to validate
            quality_score: Quality score (0-100)
            hallucination_issues: Detected hallucinations
            
        Returns:
            ValidationDecisionResult
        """
        # Check for critical hallucinations
        critical_hallucinations = [
            issue for issue in hallucination_issues
            if issue.severity == "CRITICAL"
        ]
        
        if critical_hallucinations:
            # Auto-reject
            return ValidationDecisionResult(
                decision=ValidationDecision.REJECTED,
                needs_review=False,
                quality_score=quality_score,
                reason="Critical hallucination detected",
                auto_decision=True,
            )
        
        # Check quality score
        if quality_score >= self.auto_approve_threshold:
            # Auto-approve (high quality)
            return ValidationDecisionResult(
                decision=ValidationDecision.APPROVED,
                needs_review=False,
                quality_score=quality_score,
                reason="High quality score",
                auto_decision=True,
            )
        
        elif quality_score < self.quality_threshold:
            # Needs human review (low quality)
            return ValidationDecisionResult(
                decision=ValidationDecision.PENDING,
                needs_review=True,
                quality_score=quality_score,
                reason=f"Quality score below threshold ({quality_score:.1f} < {self.quality_threshold})",
                auto_decision=False,
            )
        
        else:
            # Medium quality - queue for review
            return ValidationDecisionResult(
                decision=ValidationDecision.PENDING,
                needs_review=True,
                quality_score=quality_score,
                reason="Quality score requires verification",
                auto_decision=False,
            )


@dataclass
class ValidationDecisionResult:
    """Result of validation decision."""
    decision: ValidationDecision
    needs_review: bool
    quality_score: float
    reason: str
    auto_decision: bool  # True if automated, False if human review


# Export
__all__ = [
    'ValidationDecision',
    'ValidationReview',
    'ValidationQueue',
    'ValidationWorkflow',
    'ValidationDecisionResult',
]
