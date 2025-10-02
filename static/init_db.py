"""Database initialization script."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from models import User, Query, Feedback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database with tables and sample data."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        logger.info("Creating database tables...")
        db.create_all()
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created tables: {tables}")
        
        # Create sample user (optional)
        if User.query.count() == 0:
            logger.info("Creating sample user...")
            sample_user = User(
                email='demo@example.com',
                password_hash='$2b$12$LQJvPysJL2XVJE6HGOhEH.2dL3zfVp4hqZ3LPxLPGm3EBXm9xfbSe',  # password: demo123
                name='Demo User'
            )
            db.session.add(sample_user)
            db.session.commit()
            logger.info("Sample user created (email: demo@example.com, password: demo123)")
        
        logger.info("Database initialization complete!")
        
        # Create necessary directories
        directories = [
            'uploads',
            'logs',
            'knowledge_base/ncert',
            'knowledge_base/formulas',
            'knowledge_base/past_papers',
            'knowledge_base/index'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")


if __name__ == '__main__':
    init_database()
