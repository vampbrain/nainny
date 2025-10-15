"""Core package initialization.

This module intentionally avoids importing database helper functions at import-time
to prevent circular import problems (models import database). Database symbols
are resolved lazily via module-level __getattr__.
"""

from importlib import import_module
from app.core.config import settings, validate_age_range, validate_complexity, validate_culture
from app.core.exceptions import *  # re-export exceptions

__all__ = [
    # Config
    'settings',
    'validate_age_range',
    'validate_complexity',
    'validate_culture',
    # Database helpers (resolved lazily)
    'get_db',
    'get_db_dependency',
    'init_db',
    'reset_db',
    'backup_db',
    'get_db_stats',
]


_LAZY_DB_SYMBOLS = {
    'get_db',
    'get_db_dependency',
    'init_db',
    'reset_db',
    'backup_db',
    'get_db_stats',
}


def __getattr__(name: str):
    """Lazily import database helper attributes from app.core.database."""
    if name in _LAZY_DB_SYMBOLS:
        module = import_module('app.core.database')
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
