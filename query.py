"""Query model."""

from datetime import datetime
from . import db


class Query(db.Model):
    """Query model for storing user questions and solutions."""
    
    __tablename__ = 'queries'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    input_type = db.Column(db.String(20), nullable=False)  # text, audio, image
    query_text = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50))  # physics, chemistry, mathematics
    topic = db.Column(db.String(100))
    query_type = db.Column(db.String(50))  # mcq, numerical, general, etc.
    
    # Solution data
    solution = db.Column(db.JSON)  # Structured solution data
    raw_solution = db.Column(db.Text)  # Raw text solution
    confidence_score = db.Column(db.Float)
    context_used = db.Column(db.JSON)  # RAG context that was used
    
    # File paths
    audio_path = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processing_time = db.Column(db.Float)  # in seconds
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # Relationships
    feedback = db.relationship('Feedback', backref='query', lazy='dynamic')
    
    def __repr__(self):
        return f'<Query {self.id}>'
    
    def to_dict(self):
        """Convert query to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'input_type': self.input_type,
            'query_text': self.query_text[:200] if self.query_text else None,
            'subject': self.subject,
            'topic': self.topic,
            'query_type': self.query_type,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_time': self.processing_time
        }
