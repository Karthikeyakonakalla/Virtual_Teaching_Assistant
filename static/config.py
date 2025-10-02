"""Configuration settings for VTA JEE application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/vta_jee.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Local Solution Generator
    LOCAL_MODE = True
    ENABLE_PATTERN_MATCHING = os.getenv('ENABLE_PATTERN_MATCHING', 'true').lower() == 'true'
    
    # File uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}
    
    # Audio settings
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
    AUDIO_MAX_DURATION = int(os.getenv('AUDIO_MAX_DURATION', 60))
    
    # Vector database
    FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'knowledge_base/index/faiss_index')
    
    # Knowledge base paths
    NCERT_PATH = Path(os.getenv('NCERT_PATH', 'knowledge_base/ncert'))
    FORMULAS_PATH = Path(os.getenv('FORMULAS_PATH', 'knowledge_base/formulas'))
    PAST_PAPERS_PATH = Path(os.getenv('PAST_PAPERS_PATH', 'knowledge_base/past_papers'))
    
    # Groq API Configuration (replaces local Ollama)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')
    GROQ_EMBEDDING_MODEL = os.getenv('GROQ_EMBEDDING_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')
    
    # Model configuration
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2048))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', 5))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
