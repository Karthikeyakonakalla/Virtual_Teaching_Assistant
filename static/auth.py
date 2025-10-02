"""Authentication API endpoints."""

import logging
import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError

from models import User, db

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user.
    
    Expected JSON:
    - email: User email
    - password: User password
    - name: User full name
    
    Returns:
        JSON response with registration status
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['email', 'password', 'name']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create new user
        user = User(
            email=data['email'],
            password_hash=password_hash,
            name=data['name']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Email already registered'
        }), 400
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user.
    
    Expected JSON:
    - email: User email
    - password: User password
    
    Returns:
        JSON response with login status and token
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Check password
        if not bcrypt.checkpw(
            data['password'].encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout a user.
    
    Returns:
        JSON response with logout status
    """
    # In a stateless JWT system, logout is handled client-side
    # by removing the token. This endpoint is for logging purposes.
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify a JWT token.
    
    Returns:
        JSON response with verification status
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'No authorization header'
            }), 401
        
        # Extract token
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header format'
            }), 401
        
        # Decode token
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Get user
            user = User.query.get(payload['user_id'])
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'Token expired'
            }), 401
            
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_token(user_id):
    """Generate JWT token for user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token


def require_auth(f):
    """Decorator to require authentication for routes.
    
    Args:
        f: Route function
        
    Returns:
        Decorated function
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Add user_id to request context
            request.user_id = payload['user_id']
            
        except (IndexError, jwt.InvalidTokenError):
            return jsonify({
                'success': False,
                'error': 'Invalid authentication'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
