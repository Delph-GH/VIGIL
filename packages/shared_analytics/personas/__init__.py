"""
shared_analytics.personas

Persona modeling engine for content-persona matching.

Base framework that platforms extend with specific profiles.
"""

from .base_persona import (
    PersonaProfile,
    ContentMatch,
    BasePersona,
)
from .modeling_engine import (
    PersonaModelingEngine,
)

__all__ = [
    # Base framework
    "PersonaProfile",
    "ContentMatch",
    "BasePersona",
    
    # Modeling engine
    "PersonaModelingEngine",
]
