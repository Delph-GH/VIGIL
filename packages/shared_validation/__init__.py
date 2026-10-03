"""
shared_validation

Article validation system with anti-hallucination detection and quality scoring.

Provides:
- HallucinationDetector: Detect LLM hallucinations
- QualityScorer: Score article quality with rules
- ValidationQueue: Human validation workflows
- ValidationWorkflow: Combined auto + human validation

Usage:
    from shared_validation import (
        HallucinationDetector,
        QualityScorer,
        ValidationWorkflow,
    )
    
    # Check for hallucinations
    detector = HallucinationDetector()
    issues = detector.detect(article)
    
    # Score quality
    scorer = QualityScorer()
    score, results = scorer.score(article)
    
    # Process through workflow
    workflow = ValidationWorkflow()
    decision = workflow.process_article(article, score, issues)
"""

from .anti_hallucination import (
    HallucinationDetector,
    HallucinationIssue,
    validate_article,
)
from .quality_scorer import (
    QualityRule,
    QualityCheckResult,
    QualityScorer,
    score_article,
)
from .human_validation import (
    ValidationDecision,
    ValidationReview,
    ValidationQueue,
    ValidationWorkflow,
    ValidationDecisionResult,
)

__version__ = "0.1.0"

__all__ = [
    # Anti-hallucination
    "HallucinationDetector",
    "HallucinationIssue",
    "validate_article",
    
    # Quality scoring
    "QualityRule",
    "QualityCheckResult",
    "QualityScorer",
    "score_article",
    
    # Human validation
    "ValidationDecision",
    "ValidationReview",
    "ValidationQueue",
    "ValidationWorkflow",
    "ValidationDecisionResult",
]
