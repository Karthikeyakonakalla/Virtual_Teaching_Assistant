"""Feedback API endpoints."""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import Feedback, Query, db
from .auth import require_auth

logger = logging.getLogger(__name__)

# Create blueprint
feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback', methods=['POST'])
@require_auth
def submit_feedback():
    """Submit feedback for a query response.
    
    Expected JSON:
    - query_id: ID of the query
    - rating: Rating (1-5)
    - comment: Optional feedback comment
    - issue_type: Optional issue type (wrong_answer, unclear, incomplete, etc.)
    
    Returns:
        JSON response with feedback submission status
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'query_id' not in data or 'rating' not in data:
            return jsonify({
                'success': False,
                'error': 'query_id and rating are required'
            }), 400
        
        # Validate rating
        rating = data.get('rating')
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }), 400
        
        # Check if query exists
        query = Query.query.get(data['query_id'])
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query not found'
            }), 404
        
        # Create feedback
        feedback = Feedback(
            query_id=data['query_id'],
            user_id=request.user_id,
            rating=rating,
            comment=data.get('comment', ''),
            issue_type=data.get('issue_type'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        logger.info(f"Feedback submitted for query {data['query_id']} by user {request.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.id
        }), 201
        
    except SQLAlchemyError as e:
        logger.error(f"Database error submitting feedback: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error'
        }), 500
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/feedback/<int:feedback_id>', methods=['GET'])
@require_auth
def get_feedback(feedback_id):
    """Get a specific feedback entry.
    
    Args:
        feedback_id: ID of the feedback
        
    Returns:
        JSON response with feedback details
    """
    try:
        feedback = Feedback.query.get(feedback_id)
        
        if not feedback:
            return jsonify({
                'success': False,
                'error': 'Feedback not found'
            }), 404
        
        # Check if user has permission to view this feedback
        if feedback.user_id != request.user_id:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        return jsonify({
            'success': True,
            'feedback': {
                'id': feedback.id,
                'query_id': feedback.query_id,
                'rating': feedback.rating,
                'comment': feedback.comment,
                'issue_type': feedback.issue_type,
                'created_at': feedback.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Get aggregated feedback statistics.
    
    Returns:
        JSON response with feedback statistics
    """
    try:
        # Calculate average rating
        avg_rating = db.session.query(
            db.func.avg(Feedback.rating)
        ).scalar() or 0
        
        # Count total feedback
        total_feedback = Feedback.query.count()
        
        # Rating distribution
        rating_dist = db.session.query(
            Feedback.rating,
            db.func.count(Feedback.rating)
        ).group_by(Feedback.rating).all()
        
        rating_distribution = {
            str(rating): count for rating, count in rating_dist
        }
        
        # Issue type distribution
        issue_dist = db.session.query(
            Feedback.issue_type,
            db.func.count(Feedback.issue_type)
        ).filter(
            Feedback.issue_type.isnot(None)
        ).group_by(Feedback.issue_type).all()
        
        issue_distribution = {
            issue_type: count for issue_type, count in issue_dist
        }
        
        return jsonify({
            'success': True,
            'stats': {
                'average_rating': round(float(avg_rating), 2),
                'total_feedback': total_feedback,
                'rating_distribution': rating_distribution,
                'issue_distribution': issue_distribution
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating feedback stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/feedback/recent', methods=['GET'])
def get_recent_feedback():
    """Get recent feedback entries.
    
    Query params:
    - limit: Number of entries to return (default 10, max 50)
    - offset: Offset for pagination (default 0)
    
    Returns:
        JSON response with recent feedback
    """
    try:
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 10)), 50)
        offset = int(request.args.get('offset', 0))
        
        # Query recent feedback
        feedback_entries = Feedback.query.order_by(
            Feedback.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Format response
        feedback_list = []
        for feedback in feedback_entries:
            feedback_list.append({
                'id': feedback.id,
                'query_id': feedback.query_id,
                'rating': feedback.rating,
                'comment': feedback.comment[:100] if feedback.comment else '',
                'issue_type': feedback.issue_type,
                'created_at': feedback.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'feedback': feedback_list,
            'count': len(feedback_list),
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error retrieving recent feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/feedback/<int:feedback_id>', methods=['DELETE'])
@require_auth
def delete_feedback(feedback_id):
    """Delete a feedback entry.
    
    Args:
        feedback_id: ID of the feedback to delete
        
    Returns:
        JSON response with deletion status
    """
    try:
        feedback = Feedback.query.get(feedback_id)
        
        if not feedback:
            return jsonify({
                'success': False,
                'error': 'Feedback not found'
            }), 404
        
        # Check if user has permission to delete this feedback
        if feedback.user_id != request.user_id:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        db.session.delete(feedback)
        db.session.commit()
        
        logger.info(f"Feedback {feedback_id} deleted by user {request.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting feedback: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
