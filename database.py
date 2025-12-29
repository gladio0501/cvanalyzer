"""
Database configuration and session management for CVAnalyzer.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration manager."""
    
    def __init__(self):
        # Get database URL from environment or use SQLite for development
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///cvanalyzer.db')
        
        # SQLite-specific configuration for development
        if self.database_url.startswith('sqlite'):
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
            )
        else:
            # PostgreSQL configuration for production
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
            )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
    
    def create_tables(self):
        """Create all database tables."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables. USE WITH CAUTION!"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def close_session(self):
        """Close the scoped session."""
        self.SessionLocal.remove()


# Global database instance
db_config = DatabaseConfig()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and session cleanup.
    """
    session = db_config.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """
    Initialize the database by creating all tables.
    Should be called when the application starts.
    """
    try:
        db_config.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db():
    """
    Dependency for FastAPI to get database session.
    Yields a session and ensures it's closed after use.
    """
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()


# Database utility functions
def create_user(session, email, name, oauth_provider, oauth_id, profile_picture=None):
    """
    Create a new user or return existing user.
    """
    from models import User
    from datetime import datetime
    
    # Check if user already exists
    user = session.query(User).filter_by(
        oauth_provider=oauth_provider,
        oauth_id=oauth_id
    ).first()
    
    if user:
        # Update existing user
        user.email = email
        user.name = name
        user.profile_picture = profile_picture
        user.last_login = datetime.utcnow()
        logger.info(f"Updated existing user: {email}")
    else:
        # Create new user
        user = User(
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            profile_picture=profile_picture,
            last_login=datetime.utcnow()
        )
        session.add(user)
        logger.info(f"Created new user: {email}")
    
    session.commit()
    return user


def get_user_by_id(session, user_id):
    """Get user by ID."""
    from models import User
    return session.query(User).filter_by(id=user_id).first()


def get_user_by_email(session, email):
    """Get user by email."""
    from models import User
    return session.query(User).filter_by(email=email).first()


def get_user_by_oauth(session, oauth_provider, oauth_id):
    """Get user by OAuth provider and ID."""
    from models import User
    return session.query(User).filter_by(
        oauth_provider=oauth_provider,
        oauth_id=oauth_id
    ).first()


if __name__ == '__main__':
    # Initialize database when run directly
    logging.basicConfig(level=logging.INFO)
    init_database()
    print("Database initialized successfully!")
    print(f"Database URL: {db_config.database_url}")
