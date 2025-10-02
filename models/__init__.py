"""Data models for VTA JEE."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .query import Query
from .feedback import Feedback

__all__ = ['db', 'User', 'Query', 'Feedback']
