"""
shared_ai/nlp/ner.py

Named Entity Recognition for French political content.

Extracted from Vigil's processing/nlp/ner.py

Extracts:
- Persons (politicians, officials)
- Organizations (parties, ministries)
- Locations (cities, countries)
- Geopolitical entities (GPE)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "PER"           # Person names
    ORGANIZATION = "ORG"     # Organizations
    LOCATION = "LOC"         # Locations
    GPE = "GPE"              # Geopolitical entities
    DATE = "DATE"            # Dates
    EVENT = "EVENT"          # Events
    MISC = "MISC"            # Miscellaneous


@dataclass
class Entity:
    """
    Named entity.
    
    Attributes:
        text: Entity text
        type: Entity type
        start: Start position in text
        end: End position in text
        confidence: Confidence score (0-1)
        label: Original spaCy label
    """
    text: str
    type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    label: Optional[str] = None


class NamedEntityRecognizer:
    """
    Named Entity Recognition using spaCy.
    
    Extracts political entities from French text:
    - Politicians and officials
    - Political parties
    - Ministries and institutions
    - Locations
    
    Usage:
        ner = NamedEntityRecognizer(language="fr")
        
        entities = ner.extract_entities(text)
        
        for entity in entities:
            print(f"{entity.text} ({entity.type.value})")
        
        # Get entities by type
        people = ner.get_entities_by_type(entities, EntityType.PERSON)
        orgs = ner.get_entities_by_type(entities, EntityType.ORGANIZATION)
    """
    
    def __init__(
        self,
        language: str = "fr",
        model_name: Optional[str] = None,
        min_confidence: float = 0.5,
    ):
        """
        Initialize NER.
        
        Args:
            language: Language code
            model_name: spaCy model name
            min_confidence: Minimum confidence threshold
        """
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required for NER")
        
        self.language = language
        self.min_confidence = min_confidence
        
        # Load spaCy model
        if model_name is None:
            model_name = self._get_default_model(language)
        
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise ValueError(f"spaCy model '{model_name}' not found")
    
    def _get_default_model(self, language: str) -> str:
        """Get default model for language."""
        models = {
            'fr': 'fr_core_news_md',
            'en': 'en_core_web_md',
            'de': 'de_core_news_md',
        }
        return models.get(language, 'fr_core_news_md')
    
    def _map_spacy_label(self, label: str) -> EntityType:
        """Map spaCy label to EntityType."""
        mapping = {
            'PER': EntityType.PERSON,
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'LOC': EntityType.LOCATION,
            'GPE': EntityType.GPE,
            'DATE': EntityType.DATE,
            'EVENT': EntityType.EVENT,
        }
        return mapping.get(label, EntityType.MISC)
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of Entity objects
        """
        if not text:
            return []
        
        # Process with spaCy
        doc = self.nlp(text)
        
        entities = []
        
        for ent in doc.ents:
            # Map label to EntityType
            entity_type = self._map_spacy_label(ent.label_)
            
            # Create Entity object
            entity = Entity(
                text=ent.text,
                type=entity_type,
                start=ent.start_char,
                end=ent.end_char,
                label=ent.label_,
            )
            
            entities.append(entity)
        
        return entities
    
    def get_entities_by_type(
        self,
        entities: List[Entity],
        entity_type: EntityType,
    ) -> List[Entity]:
        """
        Filter entities by type.
        
        Args:
            entities: List of entities
            entity_type: Type to filter
            
        Returns:
            Filtered entities
        """
        return [e for e in entities if e.type == entity_type]
    
    def extract_people(self, text: str) -> List[str]:
        """
        Extract person names from text.
        
        Args:
            text: Input text
            
        Returns:
            List of person names
        """
        entities = self.extract_entities(text)
        people = self.get_entities_by_type(entities, EntityType.PERSON)
        return [e.text for e in people]
    
    def extract_organizations(self, text: str) -> List[str]:
        """
        Extract organization names from text.
        
        Args:
            text: Input text
            
        Returns:
            List of organization names
        """
        entities = self.extract_entities(text)
        orgs = self.get_entities_by_type(entities, EntityType.ORGANIZATION)
        return [e.text for e in orgs]
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location names from text.
        
        Args:
            text: Input text
            
        Returns:
            List of location names
        """
        entities = self.extract_entities(text)
        locs = self.get_entities_by_type(entities, EntityType.LOCATION)
        gpes = self.get_entities_by_type(entities, EntityType.GPE)
        return [e.text for e in locs + gpes]
    
    def get_entity_counts(self, entities: List[Entity]) -> Dict[EntityType, int]:
        """
        Count entities by type.
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary of counts by type
        """
        counts = {}
        
        for entity in entities:
            if entity.type not in counts:
                counts[entity.type] = 0
            counts[entity.type] += 1
        
        return counts
    
    def extract_political_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract political entities (convenience method).
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with people, organizations, locations
        """
        entities = self.extract_entities(text)
        
        return {
            'people': [e.text for e in self.get_entities_by_type(entities, EntityType.PERSON)],
            'organizations': [e.text for e in self.get_entities_by_type(entities, EntityType.ORGANIZATION)],
            'locations': [e.text for e in self.get_entities_by_type(entities, EntityType.LOCATION)],
            'gpe': [e.text for e in self.get_entities_by_type(entities, EntityType.GPE)],
        }


# Export
__all__ = [
    'NamedEntityRecognizer',
    'Entity',
    'EntityType',
]
