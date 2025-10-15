"""Services package initialization.

This module lazily imports service classes and factory functions to avoid
import-time side-effects and circular imports.
"""

from importlib import import_module

__all__ = [
    'ConceptNetService',
    'get_conceptnet_service',
    'StoryParser',
    'get_story_parser',
    'CulturalAnalyzer',
    'get_cultural_analyzer',
]

_LAZY_MAP = {
    'ConceptNetService': 'app.services.conceptnet',
    'get_conceptnet_service': 'app.services.conceptnet',
    'StoryParser': 'app.services.story_parser',
    'get_story_parser': 'app.services.story_parser',
    'CulturalAnalyzer': 'app.services.cultural_analyser',
    'get_cultural_analyzer': 'app.services.cultural_analyser',
}


def __getattr__(name: str):
    if name in _LAZY_MAP:
        module = import_module(_LAZY_MAP[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
