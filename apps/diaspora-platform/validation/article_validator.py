"""
apps/diaspora-platform/validation/article_validator.py

Diaspora-specific validation using shared_validation.

Integrates:
- Anti-hallucination detection
- Quality scoring
- Human validation workflows

Replaces: validation/validator.py
"""

from typing import Dict, List, Tuple, Optional
from shared_types import ScrapedArticle, ArticleStatus
from shared_validation import (
    HallucinationDetector,
    QualityScorer,
    QualityRule,
    ValidationWorkflow,
    ValidationQueue,
    ValidationDecision,
    validate_article,
    score_article,
)
from shared_utils import get_current_timestamp


class DiasporaArticleValidator:
    """
    Diaspora-specific article validator.
    
    Uses shared_validation with Diaspora customizations:
    - Expat community focus validation
    - French/German language checks
    - Cross-border content validation
    
    Usage:
        validator = DiasporaArticleValidator()
        
        result = validator.validate_article(article)
        
        if result['approved']:
            publish(article)
        elif result['needs_review']:
            queue_for_review(article, result['reason'])
    """
    
    def __init__(
        self,
        quality_threshold: float = 70.0,
        enable_human_validation: bool = True,
    ):
        """
        Initialize validator.
        
        Args:
            quality_threshold: Minimum quality score for approval
            enable_human_validation: Enable human review workflows
        """
        self.quality_threshold = quality_threshold
        
        # Initialize shared validation components
        self.hallucination_detector = HallucinationDetector()
        self.quality_scorer = self._create_quality_scorer()
        
        if enable_human_validation:
            self.validation_queue = ValidationQueue()
            self.workflow = ValidationWorkflow(
                quality_threshold=quality_threshold,
                auto_approve_threshold=90.0,
            )
        else:
            self.validation_queue = None
            self.workflow = None
    
    def _create_quality_scorer(self) -> QualityScorer:
        """Create quality scorer with Diaspora-specific rules."""
        scorer = QualityScorer()
        
        # Add Diaspora-specific rules
        from shared_types import ValidationRule, Language
        
        # Prefer French or German content
        scorer.add_rule(QualityRule(
            name="language_check",
            severity=ValidationRule.MINOR,
            description="Content should be in French or German",
            check_function=lambda a: (
                not a.language or a.language in [Language.FRENCH, Language.GERMAN],
                f"Language: {a.language.value if a.language else 'unknown'}"
            ),
            weight=0.3,
        ))
        
        return scorer
    
    def validate_article(self, article: ScrapedArticle) -> Dict[str, any]:
        """
        Validate article through complete workflow.
        
        Args:
            article: Article to validate
            
        Returns:
            Dictionary with validation results
        """
        # 1. Check hallucinations
        is_valid, hallucination_issues = validate_article(article)
        
        # 2. Score quality
        quality_score, quality_details = score_article(article)
        
        # Use custom scorer for Diaspora-specific checks
        diaspora_score, diaspora_results = self.quality_scorer.score(article)
        
        # Take minimum of scores (most conservative)
        final_score = min(quality_score, diaspora_score)
        
        # 3. Process through workflow if enabled
        if self.workflow:
            decision = self.workflow.process_article(
                article=article,
                quality_score=final_score,
                hallucination_issues=hallucination_issues,
            )
            
            # Add to queue if needs review
            if decision.needs_review and self.validation_queue:
                self.validation_queue.add(
                    article,
                    quality_score=final_score,
                    reason=decision.reason,
                )
            
            return {
                'approved': decision.decision == ValidationDecision.APPROVED,
                'rejected': decision.decision == ValidationDecision.REJECTED,
                'needs_review': decision.needs_review,
                'quality_score': final_score,
                'hallucination_issues': len(hallucination_issues),
                'critical_hallucinations': len([i for i in hallucination_issues if i.severity == "CRITICAL"]),
                'decision': decision.decision.value,
                'reason': decision.reason,
                'auto_decision': decision.auto_decision,
            }
        else:
            # Manual decision without workflow
            critical_hallucinations = [i for i in hallucination_issues if i.severity == "CRITICAL"]
            
            if critical_hallucinations:
                approved = False
                needs_review = False
                reason = "Critical hallucination detected"
            elif final_score >= 90:
                approved = True
                needs_review = False
                reason = "High quality"
            elif final_score >= self.quality_threshold:
                approved = False
                needs_review = True
                reason = "Medium quality - needs review"
            else:
                approved = False
                needs_review = True
                reason = f"Low quality ({final_score:.1f})"
            
            return {
                'approved': approved,
                'rejected': len(critical_hallucinations) > 0,
                'needs_review': needs_review,
                'quality_score': final_score,
                'hallucination_issues': len(hallucination_issues),
                'critical_hallucinations': len(critical_hallucinations),
                'reason': reason,
            }
    
    def get_review_queue_stats(self) -> Dict[str, any]:
        """Get statistics for human review queue."""
        if not self.validation_queue:
            return {'error': 'Human validation not enabled'}
        
        return self.validation_queue.get_queue_stats()


# Export
__all__ = ['DiasporaArticleValidator']
