"""
apps/vigil-platform/validation/article_validator.py

Vigil-specific validation using shared_validation.

Integrates:
- Anti-hallucination detection
- Quality scoring
- Human validation workflows
- Political content validation

Replaces: validation/quality_scorer.py
"""

from typing import Dict, List, Optional
from shared_types import ScrapedArticle, ArticleStatus, SourceCategory
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


class VigilArticleValidator:
    """
    Vigil-specific article validator.
    
    Uses shared_validation with Vigil customizations:
    - Political content validation
    - Entity extraction integration (separate module)
    - Parliamentary source verification
    
    Usage:
        validator = VigilArticleValidator()
        
        result = validator.validate_article(article)
        
        if result['approved']:
            process_for_nlp(article)
        elif result['needs_review']:
            queue_for_review(article)
    """
    
    def __init__(
        self,
        quality_threshold: float = 75.0,  # Higher threshold for political content
        enable_human_validation: bool = True,
        strict_mode: bool = True,  # Strict validation for political content
    ):
        """
        Initialize validator.
        
        Args:
            quality_threshold: Minimum quality score (higher for politics)
            enable_human_validation: Enable human review workflows
            strict_mode: Enable strict validation for political content
        """
        self.quality_threshold = quality_threshold
        self.strict_mode = strict_mode
        
        # Initialize shared validation components
        self.hallucination_detector = HallucinationDetector(strict_mode=strict_mode)
        self.quality_scorer = self._create_quality_scorer()
        
        if enable_human_validation:
            self.validation_queue = ValidationQueue()
            self.workflow = ValidationWorkflow(
                quality_threshold=quality_threshold,
                auto_approve_threshold=95.0,  # Higher for political content
            )
        else:
            self.validation_queue = None
            self.workflow = None
    
    def _create_quality_scorer(self) -> QualityScorer:
        """Create quality scorer with Vigil-specific rules."""
        scorer = QualityScorer()
        
        # Add Vigil-specific rules
        from shared_types import ValidationRule, Language
        
        # Must be French content (political focus)
        scorer.add_rule(QualityRule(
            name="french_content",
            severity=ValidationRule.MAJOR,
            description="Political content must be in French",
            check_function=lambda a: (
                a.language == Language.FRENCH,
                f"Language: {a.language.value if a.language else 'unknown'}"
            ),
            weight=0.8,
        ))
        
        # Political articles should have publication date
        scorer.add_rule(QualityRule(
            name="has_publication_date_political",
            severity=ValidationRule.MAJOR if self.strict_mode else ValidationRule.MINOR,
            description="Political articles should have publication date",
            check_function=lambda a: (
                bool(a.publication_date),
                "Date present" if a.publication_date else "Date missing"
            ),
            weight=0.7,
        ))
        
        # Should have substantial content for political analysis
        scorer.add_rule(QualityRule(
            name="substantial_political_content",
            severity=ValidationRule.MAJOR,
            description="Political article should have substantial content (>200 chars)",
            check_function=lambda a: (
                bool(a.body_text and len(a.body_text.strip()) > 200),
                f"Content length: {len(a.body_text) if a.body_text else 0} chars"
            ),
            weight=0.6,
        ))
        
        return scorer
    
    def validate_article(
        self,
        article: ScrapedArticle,
        source_category: Optional[SourceCategory] = None,
    ) -> Dict[str, any]:
        """
        Validate article through complete workflow.
        
        Args:
            article: Article to validate
            source_category: Source category (for enhanced validation)
            
        Returns:
            Dictionary with validation results
        """
        # 1. Check hallucinations (strict for political content)
        is_valid, hallucination_issues = validate_article(article)
        
        # 2. Score quality
        quality_score, quality_details = score_article(article)
        
        # Use custom scorer for Vigil-specific checks
        vigil_score, vigil_results = self.quality_scorer.score(article)
        
        # Take minimum of scores (most conservative)
        final_score = min(quality_score, vigil_score)
        
        # 3. Apply category-specific adjustments
        if source_category in [SourceCategory.PARLIAMENTARY, SourceCategory.GOVERNMENT]:
            # Official sources should have higher quality
            if final_score < 80:
                final_score *= 0.9  # Slight penalty for low-quality official sources
        
        # 4. Process through workflow if enabled
        if self.workflow:
            decision = self.workflow.process_article(
                article=article,
                quality_score=final_score,
                hallucination_issues=hallucination_issues,
            )
            
            # Add to queue if needs review
            if decision.needs_review and self.validation_queue:
                priority = None
                if source_category in [SourceCategory.PARLIAMENTARY, SourceCategory.GOVERNMENT]:
                    priority = 90  # High priority for official sources
                
                self.validation_queue.add(
                    article,
                    quality_score=final_score,
                    reason=decision.reason,
                    priority=priority,
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
                'source_category': source_category.value if source_category else None,
            }
        else:
            # Manual decision without workflow
            critical_hallucinations = [i for i in hallucination_issues if i.severity == "CRITICAL"]
            
            if critical_hallucinations:
                approved = False
                needs_review = False
                reason = "Critical hallucination detected"
            elif final_score >= 95:
                approved = True
                needs_review = False
                reason = "Excellent quality"
            elif final_score >= self.quality_threshold:
                approved = False
                needs_review = True
                reason = "Good quality - verification recommended"
            else:
                approved = False
                needs_review = True
                reason = f"Quality below threshold ({final_score:.1f})"
            
            return {
                'approved': approved,
                'rejected': len(critical_hallucinations) > 0,
                'needs_review': needs_review,
                'quality_score': final_score,
                'hallucination_issues': len(hallucination_issues),
                'critical_hallucinations': len(critical_hallucinations),
                'reason': reason,
                'source_category': source_category.value if source_category else None,
            }
    
    def get_review_queue_stats(self) -> Dict[str, any]:
        """Get statistics for human review queue."""
        if not self.validation_queue:
            return {'error': 'Human validation not enabled'}
        
        return self.validation_queue.get_queue_stats()


# Export
__all__ = ['VigilArticleValidator']
