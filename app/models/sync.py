"""Synchronization and cache models.

Canonical single-definition module for caching and sync models used by the
application. Keep this file minimal and avoid duplicating class definitions
or embedding code blocks inside it.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ConceptNetCache(Base):
    __tablename__ = "conceptnet_cache"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String(255), nullable=False, unique=True, index=True)
    relations = Column(JSON)
    last_updated = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now())
    access_count = Column(Integer, default=0)
    is_complete = Column(String(50), default="partial")

    def __repr__(self):
        return f"<ConceptNetCache(concept={self.concept})>"


class SyncQueue(Base):
    __tablename__ = "sync_queue"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(100), nullable=False)
    payload = Column(JSON)
    priority = Column(Integer, default=5)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SyncQueue(op={self.operation_type}, status={self.status})>"


class SystemStatus(Base):
    __tablename__ = "system_status"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    is_online = Column(String(50), default="unknown")
    last_online_check = Column(DateTime)
    last_successful_sync = Column(DateTime)
    pending_operations = Column(Integer, default=0)
    failed_operations = Column(Integer, default=0)
    cached_concepts = Column(Integer, default=0)
    cache_hit_rate = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)

    def __repr__(self):
        return f"<SystemStatus(online={self.is_online})>"
