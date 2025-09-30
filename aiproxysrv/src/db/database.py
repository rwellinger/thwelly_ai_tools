"""Database configuration and engine setup"""
import re
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL, DATABASE_ECHO
from utils.logger import logger  # Direct import to avoid circular dependency with utils.__init__

def sanitize_url_for_logging(url):
    """Remove password from URL for safe logging"""
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)

logger.info("database_connection_initiated", database_url=sanitize_url_for_logging(DATABASE_URL))
try:
    engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO)
    logger.info("database_engine_created", echo=DATABASE_ECHO)
except Exception as e:
    logger.error("database_engine_creation_failed", error=str(e), error_type=type(e).__name__)
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        logger.debug("database_session_created")
        yield db
    except Exception as e:
        logger.error("database_session_creation_failed", error=str(e), error_type=type(e).__name__)
        raise
    finally:
        try:
            db.close()
            logger.debug("database_session_closed")
        except Exception as e:
            logger.error("database_session_close_failed", error=str(e), error_type=type(e).__name__)