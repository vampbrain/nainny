"""User models: preferences and interaction history."""

from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from datetime import datetime
from app.core.database import Base


class UserPreference(Base):
    __tablename__ = 'user_preferences'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    preferred_culture = Column(String(80), default='indian')
    preferred_age_range = Column(String(20), default='all')
    preferred_language = Column(String(50), default='en')
    complexity_preference = Column(Integer, default=5)
    custom_settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserPreference(user_id='{self.user_id}', culture='{self.preferred_culture}')>"


class InteractionHistory(Base):
    __tablename__ = 'interaction_history'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    action = Column(String(255))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InteractionHistory(user_id='{self.user_id}', action='{self.action}')>"
