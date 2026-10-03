"""
shared_validation/quality_scorer.py

Quality scoring system with configurable rules.

Extracted from Vigil's validation/quality_scorer.py

Scores articles based on:
- Completeness (required fields present)
- Content quality (length, structure)
- Metadata quality
- Source reliability
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from shared_types import ScrapedArticle, ValidationRule


class QualityRule:
    """
    Single quality validation rule.
    
    Rules check specific aspects of article quality
    and assign scores/penalties.
    """
    
    def __init__(
        self,
        name: str,
        severity: ValidationRule,
        description: str,
        check_function,
        weight: float = 1.0,
    ):
        """
        Initialize rule.
        
        Args:
            name: Rule identifier
            severity: CRITICAL, WARNING, or INFO
            description: Human-readable description
            check_function: Function that checks the rule
            weight: Weight in final score (0-1)
        """
        self.name = name
        self.severity = severity
        self.description = description
        self.check_function = check_function
        self.weight = weight
    
    def check(self, article: ScrapedArticle) -> 'QualityCheckResult':
        """
        Check rule against article.
        
        Args:
            article: Article to check
            
        Returns:
            QualityCheckResult
        """
        try:
            passed, message = self.check_function(article)
            return QualityCheckResult(
                rule_name=self.name,
                severity=self.severity,
                passed=passed,
                message=message or self.description,
            )
        except Exception as e:
            return QualityCheckResult(
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Rule check failed: {e}",
            )


@dataclass
class QualityCheckResult:
    """Result of a single quality check."""
    rule_name: str
    severity: ValidationRule
    passed: bool
    message: str


class QualityScorer:
    """
    Score article quality using configurable rules.
    
    Usage:
        scorer = QualityScorer()
        
        # Add custom rules
        scorer.add_rule(QualityRule(
            name="has_title",
            severity=ValidationRule.CRITICAL,
            description="Article must have title",
            check_function=lambda a: (bool(a.title), "Title present"),
        ))
        
        # Score article
        score, results = scorer.score(article)
        print(f"Quality score: {score}/100")
    """
    
    def __init__(self):
        """Initialize scorer with default rules."""
        self.rules: List[QualityRule] = []
        self._add_default_rules()
    
    def _add_default_rules(self):
        """Add default quality rules."""
        
        # CRITICAL: Must have URL
        self.add_rule(QualityRule(
            name="has_url",
            severity=ValidationRule.CRITICAL,
            description="Article must have URL",
            check_function=lambda a: (
                bool(a.url),
                "URL present" if a.url else "URL missing"
            ),
            weight=1.0,
        ))
        
        # CRITICAL: Must have title
        self.add_rule(QualityRule(
            name="has_title",
            severity=ValidationRule.CRITICAL,
            description="Article must have title",
            check_function=lambda a: (
                bool(a.title),
                "Title present" if a.title else "Title missing"
            ),
            weight=1.0,
        ))
        
        # CRITICAL: Must have body text
        self.add_rule(QualityRule(
            name="has_body",
            severity=ValidationRule.CRITICAL,
            description="Article must have body text",
            check_function=lambda a: (
                bool(a.body_text and len(a.body_text.strip()) > 0),
                "Body text present" if a.body_text else "Body text missing"
            ),
            weight=1.0,
        ))
        
        # WARNING: Should have publication date
        self.add_rule(QualityRule(
            name="has_publication_date",
            severity=ValidationRule.MAJOR,
            description="Article should have publication date",
            check_function=lambda a: (
                bool(a.publication_date),
                "Publication date present" if a.publication_date else "Publication date missing"
            ),
            weight=0.5,
        ))
        
        # WARNING: Body should be substantial (>100 chars)
        self.add_rule(QualityRule(
            name="substantial_body",
            severity=ValidationRule.MAJOR,
            description="Body text should be substantial (>100 chars)",
            check_function=lambda a: (
                bool(a.body_text and len(a.body_text.strip()) > 100),
                f"Body length: {len(a.body_text) if a.body_text else 0} chars"
            ),
            weight=0.5,
        ))
        
        # INFO: Should have author
        self.add_rule(QualityRule(
            name="has_author",
            severity=ValidationRule.MINOR,
            description="Article should have author",
            check_function=lambda a: (
                bool(a.author),
                "Author present" if a.author else "Author missing"
            ),
            weight=0.2,
        ))
        
        # INFO: Should have summary
        self.add_rule(QualityRule(
            name="has_summary",
            severity=ValidationRule.MINOR,
            description="Article should have summary",
            check_function=lambda a: (
                bool(a.summary),
                "Summary present" if a.summary else "Summary missing"
            ),
            weight=0.2,
        ))
    
    def add_rule(self, rule: QualityRule):
        """Add quality rule."""
        self.rules.append(rule)
    
    def score(self, article: ScrapedArticle) -> tuple[float, List[QualityCheckResult]]:
        """
        Score article quality.
        
        Args:
            article: Article to score
            
        Returns:
            Tuple of (score, results)
            Score is 0-100, where 100 is perfect quality
        """
        results = []
        
        # Check all rules
        for rule in self.rules:
            result = rule.check(article)
            results.append(result)
        
        # Calculate score
        score = self._calculate_score(results)
        
        return (score, results)
    
    def _calculate_score(self, results: List[QualityCheckResult]) -> float:
        """
        Calculate composite quality score.
        
        Formula:
        - CRITICAL failures: 0 score
        - WARNING failures: -20 points each
        - INFO failures: -5 points each
        - Weight applied to each rule
        
        Args:
            results: Check results
            
        Returns:
            Score (0-100)
        """
        # Check for critical failures
        critical_failures = [
            r for r in results
            if not r.passed and r.severity == ValidationRule.CRITICAL
        ]
        
        if critical_failures:
            return 0.0  # Critical failure = 0 score
        
        # Start with perfect score
        score = 100.0
        
        # Deduct for failures
        for result in results:
            if not result.passed:
                # Get corresponding rule for weight
                rule = next((r for r in self.rules if r.name == result.rule_name), None)
                weight = rule.weight if rule else 1.0
                
                if result.severity == ValidationRule.MAJOR:
                    score -= 20 * weight
                elif result.severity == ValidationRule.MINOR:
                    score -= 5 * weight
        
        # Clamp to 0-100
        return max(0.0, min(100.0, score))
    
    def get_failed_rules(
        self,
        results: List[QualityCheckResult],
        severity: Optional[ValidationRule] = None,
    ) -> List[QualityCheckResult]:
        """
        Get failed rules, optionally filtered by severity.
        
        Args:
            results: Check results
            severity: Filter by severity (None = all)
            
        Returns:
            List of failed checks
        """
        failed = [r for r in results if not r.passed]
        
        if severity:
            failed = [r for r in failed if r.severity == severity]
        
        return failed


def score_article(article: ScrapedArticle) -> tuple[float, Dict[str, any]]:
    """
    Score article quality (convenience function).
    
    Args:
        article: Article to score
        
    Returns:
        Tuple of (score, details)
    """
    scorer = QualityScorer()
    score, results = scorer.score(article)
    
    # Build details dict
    failed = [r for r in results if not r.passed]
    
    details = {
        'score': score,
        'total_checks': len(results),
        'passed': len([r for r in results if r.passed]),
        'failed': len(failed),
        'critical_failures': len([r for r in failed if r.severity == ValidationRule.CRITICAL]),
        'warnings': len([r for r in failed if r.severity == ValidationRule.MAJOR]),
        'info': len([r for r in failed if r.severity == ValidationRule.MINOR]),
        'failures': [
            {'rule': r.rule_name, 'severity': r.severity.value, 'message': r.message}
            for r in failed
        ],
    }
    
    return (score, details)


# Export
__all__ = [
    'QualityRule',
    'QualityCheckResult',
    'QualityScorer',
    'score_article',
]
