"""Database configuration and engine setup"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL, DATABASE_ECHO

print(f"Connecting to database: {DATABASE_URL[:50]}...", file=sys.stderr)
try:
    engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO)
    print("Database engine created successfully", file=sys.stderr)
except Exception as e:
    print(f"Error creating database engine: {e}", file=sys.stderr)
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        print(f"Database session created", file=sys.stderr)
        yield db
    except Exception as e:
        print(f"Error creating database session: {e}", file=sys.stderr)
        raise
    finally:
        try:
            db.close()
            print(f"Database session closed", file=sys.stderr)
        except Exception as e:
            print(f"Error closing database session: {e}", file=sys.stderr)