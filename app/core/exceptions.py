"""Project-specific exceptions for Nainny."""

class NainnyError(Exception):
    """Base class for Nainny errors."""


class NotFoundError(NainnyError):
    """Requested resource was not found."""


class ValidationError(NainnyError):
    """Validation failed for provided input."""


class ExternalServiceError(NainnyError):
    """Raised when an external dependency (e.g. ConceptNet) fails."""


class DatabaseError(NainnyError):
    """Raised for database-related issues."""
"""Custom exceptions used across the application"""

class NainnyException(Exception):
    """Base exception for the project"""
    def __init__(self, message: str, meta: dict = None):
        super().__init__(message)
        self.meta = meta or {}


class ConceptNetOfflineException(NainnyException):
    pass


class ConceptNetAPIException(NainnyException):
    pass


class ConceptNotFoundException(NainnyException):
    pass


class NLPModelNotLoadedException(NainnyException):
    pass


class StoryParsingException(NainnyException):
    pass


class CulturalContextNotFoundException(NainnyException):
    pass


class SyncException(NainnyException):
    pass
