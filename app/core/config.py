"""
Configuration management
Load settings from environment variables
"""

try:
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BaseSettings = object

from typing import Optional
import os


class Settings(BaseSettings if BaseSettings is not object else object):
    """
    Application settings
    """
    
    # Application
    APP_NAME: str = "Narrative Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DB_PATH: str = "narrative_intelligence.db"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"
    
    # ConceptNet API
    CONCEPTNET_API_BASE: str = "http://api.conceptnet.io"
    CONCEPTNET_TIMEOUT: int = 10  # seconds
    CONCEPTNET_RETRY_COUNT: int = 3
    
    # Cache settings
    CACHE_EXPIRY_DAYS: int = 30
    MAX_CACHE_SIZE_MB: int = 100
    CACHE_CLEANUP_INTERVAL: int = 86400  # 24 hours in seconds
    
    # NLP Settings
    SPACY_MODEL: str = "en_core_web_sm"
    
    # Cultural Settings (Phase 1: Indian only)
    DEFAULT_CULTURE: str = "indian"
    SUPPORTED_CULTURES: list = ["indian"]
    
    # Story Settings
    MIN_STORY_LENGTH: int = 50  # minimum words
    MAX_STORY_LENGTH: int = 5000  # maximum words
    DEFAULT_COMPLEXITY: int = 5  # 1-10 scale
    
    # Age Ranges
    AGE_RANGES: list = ["3-5", "6-8", "9-12", "13+"]
    
    # Sync Settings
    SYNC_BATCH_SIZE: int = 10  # Number of items to sync at once
    SYNC_INTERVAL: int = 300  # 5 minutes in seconds
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 60  # seconds
    
    # Offline Mode (for testing)
    FORCE_OFFLINE: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # API Settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list = ["*"]  # Configure properly in production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance. If pydantic is available it will load env values;
# otherwise we use the default attribute values defined above.
try:
    settings = Settings()
except Exception:
    # Fallback: instantiate a plain object and copy attributes from class defaults
    settings = Settings  # type: ignore



# Validation functions

def validate_age_range(age_range: str) -> bool:
    """Validate age range format"""
    return age_range in settings.AGE_RANGES


def validate_complexity(level: int) -> bool:
    """Validate complexity level (1-10)"""
    return 1 <= level <= 10


def validate_culture(culture: str) -> bool:
    """Validate culture code"""
    return culture.lower() in settings.SUPPORTED_CULTURES


def get_spacy_model_path() -> str:
    """Get path to spaCy model"""
    return settings.SPACY_MODEL


def is_offline_mode() -> bool:
    """Check if running in offline mode"""
    return settings.FORCE_OFFLINE


# Helper functions

def get_cache_expiry_seconds() -> int:
    """Get cache expiry time in seconds"""
    return settings.CACHE_EXPIRY_DAYS * 24 * 60 * 60


def get_conceptnet_url(endpoint: str = "") -> str:
    """Build ConceptNet API URL"""
    return f"{settings.CONCEPTNET_API_BASE}{endpoint}"


# Display for debugging
def print_config():
    """Print current configuration (excluding sensitive data)"""
    print(f"\n{'='*50}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"{'='*50}")
    print(f"Database: {settings.DB_PATH}")
    print(f"Culture: {settings.DEFAULT_CULTURE}")
    print(f"Cache Expiry: {settings.CACHE_EXPIRY_DAYS} days")
    print(f"Offline Mode: {settings.FORCE_OFFLINE}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"{'='*50}\n")