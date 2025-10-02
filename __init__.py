"""API package for VTA JEE."""

from .query import query_bp
from .auth import auth_bp
from .feedback import feedback_bp

__all__ = ['query_bp', 'auth_bp', 'feedback_bp']
