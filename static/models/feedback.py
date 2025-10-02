"""Feedback model."""

from datetime import datetime
from . import db


class Feedback(db.Model):
    """Feedback model for user feedback on solutions."""
    
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(36), db.ForeignKey('queries.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    issue_type = db.Column(db.String(50))  # wrong_answer, unclear, incomplete, etc.
    
    # Correction data
    correction = db.Column(db.Text)  # User-provided correct answer
    is_helpful = db.Column(db.Boolean)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id} for Query {self.query_id}>'
    
    def to_dict(self):
        """Convert feedback to dictionary."""
        return {
            'id': self.id,
            'query_id': self.query_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'issue_type': self.issue_type,
            'correction': self.correction,
            'is_helpful': self.is_helpful,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
