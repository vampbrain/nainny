"""Cultural models for Indian contexts and mappings.

This file defines the SQLAlchemy models used by the seeder and services.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, Float, Boolean
from app.core.database import Base


class CulturalContext(Base):
    __tablename__ = 'cultural_contexts'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    culture = Column(String(80), default='indian', index=True, nullable=False)
    category = Column(String(80), index=True)  # value, custom, food, symbol, etc.
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    related_concepts = Column(JSON)
    sensitivity_level = Column(String(50), default='neutral')
    age_appropriate = Column(String(20), default='all')
    examples = Column(JSON)
    storytelling_notes = Column(Text)

    def __repr__(self):
        return f"<CulturalContext(name='{self.name}', culture='{self.culture}')>"


class IndianFestival(Base):
    __tablename__ = 'indian_festivals'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    regional_names = Column(JSON)
    month = Column(String(80))
    season = Column(String(80))
    significance = Column(Text)
    story_elements = Column(JSON)
    common_activities = Column(JSON)
    traditional_foods = Column(JSON)
    decorations = Column(JSON)
    child_friendly_explanation = Column(Text)
    story_hooks = Column(JSON)
    age_appropriate = Column(String(20), default='all')
    popularity_score = Column(Float, default=0.5)

    def __repr__(self):
        return f"<IndianFestival(name='{self.name}')>"


class CulturalMapping(Base):
    __tablename__ = 'cultural_mappings'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    source_concept = Column(String(255), nullable=False)
    source_context = Column(String(80), default='generic')
    target_concept = Column(String(255), nullable=False)
    target_culture = Column(String(80), default='indian')
    mapping_type = Column(String(80), default='similar')
    confidence_score = Column(Float, default=0.5)
    explanation = Column(Text)
    usage_examples = Column(JSON)
    verified = Column(Boolean, default=False)

    def __repr__(self):
        return f"<CulturalMapping({self.source_concept} -> {self.target_concept})>"
