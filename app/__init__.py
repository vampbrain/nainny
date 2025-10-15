"""Top-level app package for the Nainny project

Expose commonly used submodules for easier imports.
"""


"""Top-level app package for the Nainny project.

Expose commonly used submodules for easier imports.
"""

from app.core.config import settings  # noqa: F401
from app.core.database import init_db, get_db, get_db_dependency  # noqa: F401

__all__ = [
    "settings",
    "init_db",
    "get_db",
    "get_db_dependency",
]
