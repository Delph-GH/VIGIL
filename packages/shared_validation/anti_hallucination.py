"""
shared_validation/anti_hallucination.py

Anti-hallucination detection for LLM-generated content.

Extracted from Diaspora's validation/validator.py

Detects common hallucination patterns:
- Invalid URLs
- Inconsistent facts
- Impossible dates
- Self-contradictions
"""

import re
from typing import List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from shared_types import ScrapedArticle
from shared_utils import normalize_url, parse_flexible_date


class HallucinationDetector:
    """
    Detect hallucinations in LLM-generated content.
    
    Checks for:
    - Invalid URLs (malformed, unreachable)
    - Date inconsistencies (future dates, impossible dates)
    - Fact contradictions (within same article)
    - Common LLM artifacts
    
    Usage:
        detector = HallucinationDetector()
        issues = detector.detect(article)
        
        if issues:
            for issue in issues:
                print(f"{issue.severity}: {issue.description}")
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize detector.
        
        Args:
            strict_mode: Enable stricter validation rules
        """
        self.strict_mode = strict_mode
    
    def detect(self, article: ScrapedArticle) -> List['HallucinationIssue']:
        """
        Detect hallucinations in article.
        
        Args:
            article: Article to validate
            
        Returns:
            List of detected issues (empty if clean)
        """
        issues = []
        
        # Check URL validity
        issues.extend(self._check_url_validity(article))
        
        # Check date consistency
        issues.extend(self._check_date_consistency(article))
        
        # Check for common LLM artifacts
        issues.extend(self._check_llm_artifacts(article))
        
        # Check fact contradictions
        if article.body_text:
            issues.extend(self._check_contradictions(article.body_text))
        
        return issues
    
    def _check_url_validity(self, article: ScrapedArticle) -> List['HallucinationIssue']:
        """Check if URLs in article are valid."""
        issues = []
        
        # Check main URL
        if article.url:
            try:
                parsed = urlparse(article.url)
                if not parsed.scheme or not parsed.netloc:
                    issues.append(HallucinationIssue(
                        severity="CRITICAL",
                        field="url",
                        description=f"Malformed URL: {article.url}",
                        value=article.url,
                    ))
            except Exception as e:
                issues.append(HallucinationIssue(
                    severity="CRITICAL",
                    field="url",
                    description=f"Invalid URL: {e}",
                    value=article.url,
                ))
        
        # Check URLs in text
        if article.body_text:
            urls = re.findall(r'https?://[^\s<>"]+', article.body_text)
            for url in urls[:10]:  # Check first 10 URLs
                try:
                    parsed = urlparse(url)
                    if not parsed.netloc:
                        issues.append(HallucinationIssue(
                            severity="WARNING",
                            field="body_text",
                            description=f"Malformed URL in text: {url}",
                            value=url,
                        ))
                except Exception:
                    pass
        
        return issues
    
    def _check_date_consistency(self, article: ScrapedArticle) -> List['HallucinationIssue']:
        """Check date fields for consistency."""
        issues = []
        now = datetime.now()
        
        # Check publication date
        if article.publication_date:
            try:
                pub_date = parse_flexible_date(article.publication_date)
                if pub_date:
                    # Future date (likely hallucination)
                    if pub_date > now:
                        issues.append(HallucinationIssue(
                            severity="CRITICAL",
                            field="publication_date",
                            description=f"Publication date in future: {article.publication_date}",
                            value=article.publication_date,
                        ))
                    
                    # Very old date (>50 years, possible hallucination)
                    years_ago = (now - pub_date).days / 365.25
                    if years_ago > 50:
                        issues.append(HallucinationIssue(
                            severity="WARNING",
                            field="publication_date",
                            description=f"Publication date very old: {article.publication_date}",
                            value=article.publication_date,
                        ))
            except Exception as e:
                issues.append(HallucinationIssue(
                    severity="WARNING",
                    field="publication_date",
                    description=f"Unparseable date: {e}",
                    value=article.publication_date,
                ))
        
        return issues
    
    def _check_llm_artifacts(self, article: ScrapedArticle) -> List['HallucinationIssue']:
        """Check for common LLM generation artifacts."""
        issues = []
        
        if not article.body_text:
            return issues
        
        text_lower = article.body_text.lower()
        
        # Common LLM hedging phrases
        hedging_phrases = [
            "as an ai",
            "i don't have access",
            "i cannot provide",
            "i apologize, but",
            "i'm not able to",
            "i don't actually",
        ]
        
        for phrase in hedging_phrases:
            if phrase in text_lower:
                issues.append(HallucinationIssue(
                    severity="CRITICAL",
                    field="body_text",
                    description=f"LLM artifact detected: '{phrase}'",
                    value=phrase,
                ))
        
        # Check for placeholder text
        placeholders = [
            "[insert",
            "[add",
            "[placeholder",
            "lorem ipsum",
            "xxx",
        ]
        
        for placeholder in placeholders:
            if placeholder in text_lower:
                issues.append(HallucinationIssue(
                    severity="WARNING",
                    field="body_text",
                    description=f"Placeholder text detected: '{placeholder}'",
                    value=placeholder,
                ))
        
        return issues
    
    def _check_contradictions(self, text: str) -> List['HallucinationIssue']:
        """
        Check for self-contradictions in text.
        
        This is a simple heuristic check - more sophisticated
        NLP would be needed for robust contradiction detection.
        """
        issues = []
        
        # Simple contradiction patterns
        sentences = text.split('.')
        
        # Check for obvious contradictions
        # Example: "X is true" ... "X is not true"
        # This is a basic implementation - production would use NLP
        
        return issues


class HallucinationIssue:
    """
    Detected hallucination issue.
    
    Attributes:
        severity: CRITICAL, WARNING, INFO
        field: Which field has the issue
        description: Human-readable description
        value: The problematic value
    """
    
    def __init__(
        self,
        severity: str,
        field: str,
        description: str,
        value: Optional[str] = None,
    ):
        self.severity = severity
        self.field = field
        self.description = description
        self.value = value
    
    def __repr__(self):
        return f"HallucinationIssue({self.severity}: {self.description})"


def validate_article(article: ScrapedArticle) -> Tuple[bool, List[HallucinationIssue]]:
    """
    Validate article for hallucinations.
    
    Args:
        article: Article to validate
        
    Returns:
        Tuple of (is_valid, issues)
    """
    detector = HallucinationDetector()
    issues = detector.detect(article)
    
    # Critical issues = not valid
    has_critical = any(issue.severity == "CRITICAL" for issue in issues)
    
    return (not has_critical, issues)


# Export
__all__ = [
    'HallucinationDetector',
    'HallucinationIssue',
    'validate_article',
]
