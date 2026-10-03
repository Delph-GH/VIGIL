"""
shared_analytics

Analytics utilities for article salience and source trust.

Modules:
- salience: Article importance scoring
- trust: Source reliability scoring
- narratives: Narrative detection and weak signals
- personas: Persona modeling engine

Extracted from both Vigil and Diaspora analytics logic.
"""

from .salience.salience_scorer import (
    SalienceScorer,
)
from .trust.trust_scorer import (
    TrustScorer,
)
from .narratives import (
    Narrative,
    NarrativeDetector,
    NarrativeEvolution,
    WeakSignal,
    WeakSignalDetector,
)
from .personas import (
    PersonaProfile,
    ContentMatch,
    BasePersona,
    PersonaModelingEngine,
)

__all__ = [
    # Salience
    "SalienceScorer",
    
    # Trust
    "TrustScorer",
    
    # Narratives
    "Narrative",
    "NarrativeDetector",
    "NarrativeEvolution",
    "WeakSignal",
    "WeakSignalDetector",
    
    # Personas
    "PersonaProfile",
    "ContentMatch",
    "BasePersona",
    "PersonaModelingEngine",
]
