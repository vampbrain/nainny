#config for db and session

from sqlalchemy import create_engine, event 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

Base = declarative_base()

# Database configuration (engine created lazily/rebuilt by _rebuild_engine)
DB_PATH = os.getenv('DB_PATH', 'narrative_intelligence.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'

# placeholders that will be created by _rebuild_engine()
engine = None
SessionLocal = None


def _set_sqlite_pragma(dbapi_con, con_record):
    cursor = dbapi_con.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes, still safe
    cursor.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
    cursor.close()


def _rebuild_engine():
    """Create a fresh SQLAlchemy engine and SessionLocal bound to current DB_PATH.

    Call this after changing the DB_PATH env var or when tests request a clean engine.
    """
    global DB_PATH, DATABASE_URL, engine, SessionLocal
    DB_PATH = os.getenv('DB_PATH', 'narrative_intelligence.db')
    DATABASE_URL = f"sqlite:///{DB_PATH}"

    # create a new engine and attach PRAGMA event
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=StaticPool,
        echo=False,
    )

    # attach PRAGMA on connect
    # remove any previous listeners by simply re-registering for the new engine
    event.listen(engine, "connect", _set_sqlite_pragma)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(reset: bool = False):
    from app.models import (
        Story, StoryConcept, StoryAdaptation,
        CulturalContext, CulturalMapping, IndianFestival,
        UserPreference, InteractionHistory,
        ConceptNetCache, SyncQueue, SystemStatus
    )
    if reset:
        # ensure a clean schema when requested (useful for tests)
        # remove the DB file if present to guarantee a fresh SQLite file
        try:
            if DB_PATH and os.path.exists(DB_PATH):
                os.remove(DB_PATH)
        except Exception:
            # fallback to drop_all if file removal isn't possible
            if engine is not None:
                Base.metadata.drop_all(bind=engine)

        # rebuild engine/session bound to the possibly-updated DB_PATH
        _rebuild_engine()
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DB_PATH}")
    
    # Initialize system status
    _init_system_status()

def _init_system_status():
    from app.models.sync import SystemStatus
    db = SessionLocal()
    try:
        status = db.query(SystemStatus).first()
        if not status:
            status = SystemStatus(
                is_online='unknown',
                pending_operations=0,
                failed_operations=0,
                cached_concepts=0,
                cache_hit_rate=0,
                total_requests=0
            )
            db.add(status)
            db.commit()
            print("✅ System status initialized")
    except Exception as e:
        db.rollback()
        print(f"⚠️  Error initializing system status: {e}")
    finally:
        db.close()
        
@contextmanager


def get_db()-> Generator[Session, None, None]:
    # to manage context. we use with getdb as db story = db.query(Story).first()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database session error: {e}")
        raise e
    finally:
        db.close() 

def get_db_dependency():
    #for fastapi endpoints
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
def reset_db():
    "drop all tables and restart"
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _init_system_status()
    print("Database reset completed.")
    
def backup_db(backup_path: str = None):
    """Create a backup of the database"""
    import shutil
    from datetime import datetime
    
    if backup_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{DB_PATH}.backup_{timestamp}"
    
    try:
        if not os.path.exists(DB_PATH):
            print(f"Database file not found: {DB_PATH}")
            return None
            
        shutil.copy2(DB_PATH, backup_path)
        print(f" Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f" Backup failed: {e}")
        return None


def get_db_stats():
    """Get database statistics"""
    from app.models import Story, CulturalContext, ConceptNetCache
    
    with get_db() as db:
        stats = {
            'stories': db.query(Story).count(),
            'cultural_contexts': db.query(CulturalContext).count(),
            'cached_concepts': db.query(ConceptNetCache).count(),
            'database_size': _get_file_size(DB_PATH)
        }
    
    return stats


def _get_file_size(filepath):
    """Get human-readable file size"""
    if not os.path.exists(filepath):
        return "0 B"
    
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing database...")
    init_db()
    print("\nDatabase stats:")
    stats = get_db_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")