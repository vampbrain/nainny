"""Story models."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    culture = Column(String(180), default="Indian", index=True, nullable=False)
    age = Column(String(20))  # like an age range 3-5
    complexity_level = Column(Integer, default=5)  # 1-10 scale

    # metadata
    themes = Column(JSON)
    wordcount = Column(Integer)
    sentencecount = Column(Integer)

    # timestamps (for syncing facility)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships (names match classes defined below)
    concepts = relationship(
        "StoryConcept", back_populates="story", cascade="all, delete-orphan"
    )

    adaptations = relationship(
        "StoryAdaptation", back_populates="original_story", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Story(id={self.id}, title='{self.title}', culture='{self.culture}')>"


class StoryConcept(Base):
    __tablename__ = "story_concepts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    concept = Column(String(255), nullable=False)
    concepttype = Column(Text)

    importance_score = Column(Float, default=0.5)  # 0-1 relevance to story
    context = Column(String(250))  # Sentence/paragraph where concept appears

    # ConceptNet enrichment
    conceptnet_relations = Column(JSON)  # Cached relations from ConceptNet

    story = relationship("Story", back_populates="concepts")

    def __repr__(self):
        return f"<StoryConcept(concept='{self.concept}', type='{self.concepttype}')>"


class StoryAdaptation(Base):
    __tablename__ = "story_adaptations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    original_story_id = Column(Integer, ForeignKey('stories.id'), nullable=False, index=True)

    # Adaptation parameters
    adapted_content = Column(Text, nullable=False)
    target_age_range = Column(String(20))
    target_complexity = Column(Integer)

    # What changed
    adaptation_type = Column(String(50))  # 'simplify', 'elaborate', 'cultural_adapt'
    changes_made = Column(JSON)  # List of specific changes with reasons

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    original_story = relationship("Story", back_populates="adaptations")

    def __repr__(self):
        return f"<StoryAdaptation(id={self.id}, type='{self.adaptation_type}')>"
